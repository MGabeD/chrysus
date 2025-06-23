import re
import json
from dateutil import parser
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import List, Dict, Any, Optional
import pandas as pd
from pathlib import Path
from langchain_core.language_models import BaseLanguageModel
from chrysus.backend.core.available_models import gemini_2, gemini_2_5
from chrysus.utils.logger import get_logger


logger = get_logger(__name__)


_MODEL_NAME = (
    "wanadzhar913/debertav3-finetuned-banking-transaction-classification-text-only"
)
_UNCATEGORIZED = {"uncategorized", "other", "", None}


def infer_and_fix_dates(df: pd.DataFrame, date_col: str = "date") -> pd.Series:
    """
    Normalize date strings to full datetime objects.
    Handles varying formats, including partial dates (like 'Feb 2').
    Infers missing years from context (by walking down the column).
    Args:
        df: DataFrame with a date column (possibly messy).
        date_col: Name of the column to fix.
    Returns:
        pd.Series of datetime objects (np.nan if could not be parsed).
    """
    fixed_dates = []
    last_full_date = None
    inferred_year = None
    for i, raw_date in enumerate(df[date_col]):
        date_str = str(raw_date).strip()
        dt = None

        try:
            dt = parser.parse(date_str, fuzzy=True, default=None)
            if dt.year == 1900 and inferred_year:
                dt = dt.replace(year=inferred_year)
        except Exception:
            dt = None

        if dt is None:
            m = re.match(r"([A-Za-z]+)\s+(\d{1,2})", date_str)
            if m and last_full_date is not None:
                month_name, day = m.groups()
                try:
                    dt = parser.parse(f"{month_name} {day} {last_full_date.year}")
                except Exception:
                    dt = None
            elif last_full_date is not None:
                dt = last_full_date

        if dt is not None:
            last_full_date = dt
            inferred_year = dt.year
        fixed_dates.append(dt)

    return pd.Series(fixed_dates, index=df.index)


class InformedTable:

    _classifier_pipe: Optional[pipeline] = None

    def __init__(self, table: List[List[Any]], user_information: Dict[str, Any], pdf_path: Path, resolver_llm: BaseLanguageModel = gemini_2_5):
        for i in range(len(table[0])):
            table[0][i] = table[0][i].lower()

        self.table = pd.DataFrame(table[1:], columns=table[0])
        self.user_information = user_information
        self.insights = []
        self.transformation_history = []
        self.pdf_path = pdf_path
        self.is_transaction_table = False
        self.resolver_llm = resolver_llm
        self._pre_process_insights()

    @classmethod
    def _get_classifier(cls) -> "pipeline":
        """Lazily instantiate the DeBERTa-V3-large classifier in fp16."""
        if cls._classifier_pipe is None:
            cls._classifier_pipe = pipeline(
                task="text-classification",
                model=AutoModelForSequenceClassification.from_pretrained(
                    _MODEL_NAME,
                    torch_dtype=torch.float16,      
                    device_map="auto",
                    load_in_8bit=False,             
                ),
                tokenizer=AutoTokenizer.from_pretrained(_MODEL_NAME),
                batch_size=64,
                truncation=True,
            )
        return cls._classifier_pipe
    
    def _classify_transactions(self) -> None:
        logger.info("Classifying transactions")
        mask = (
            self.table["txn_category"].isna()
            | self.table["txn_category"].str.lower().isin(_UNCATEGORIZED)
        )
        if not mask.any():
            return

        unc_df = self.table.loc[mask].reset_index()
        payload = json.dumps(unc_df.to_dict(orient="records"), ensure_ascii=False)

        prompt = f"""
<task>
You are given a table of uncategorized bank-transaction rows (JSON records).
Return the SAME table, in the SAME order, as a JSON list-of-lists where the
first row is the headers; only difference: supply a meaningful value in each
row’s “txn_category” cell. The txn_category column should be a generalized category
of a transaction. For example, "food", "leisure", "utilities", "salary", "rent", "transport", "health", etc.
Never give a category that is too specific Ex: Gym membership or Bank fees should be "health" or "utilities" 
No commentary. You MUST respond strictly within the provided XML tags.
</task>
<input>
{payload}
</input>
<output>
<json_table>
{{"table":[["index","date","description","amount","balance","txn_category"], ...]}}
</json_table>
</output>
""".strip()

        try:
            resp = self.resolver_llm.invoke(prompt)
            match = re.search(r"<json_table>(.*?)</json_table>", resp.content, re.DOTALL)
            if not match:
                raise ValueError("No <json_table> tags in LLM reply")
            table_json = json.loads(match.group(1))
            tbl = table_json.get("table")
            if not tbl or len(tbl) - 1 != len(unc_df):
                raise ValueError("Row-count mismatch between request and LLM reply")
            fixed_df = pd.DataFrame(tbl[1:], columns=tbl[0])
            if not unc_df['description'].tolist() == fixed_df['description'].tolist():
                raise ValueError("Row-order/content mismatch between request and LLM reply")
            self.table.loc[unc_df["index"], "txn_category"] = fixed_df["txn_category"].astype(str).values
            self.transformation_history.append(
                {
                    "step": "llm_uncategorized_fix",
                    "model": self.resolver_llm.__class__.__name__,
                    "rows": int(mask.sum()),
                }
            )
        except Exception as e:
            print(f"LLM table classification error: {e}")
            print(f"LLM response: {getattr(resp, 'content', None)}")
            raise
 
 
    def _classify_transactions_via_tuned_bert(self):
        self.is_transaction_table = True
        classifier = self._get_classifier()

        narratives = self.table["description"].fillna("").astype(str).tolist()
        raw_preds = classifier(narratives)
        labels = [
            p[0]["label"] if isinstance(p, list) else p["label"]
            for p in raw_preds
        ]
        self.table["txn_category"] = labels
        self.transformation_history.append(
            {
                "step": "txn_classification",
                "model": _MODEL_NAME,
                "rows": len(self.table),
            }
        ) 

    def _pre_process_insights(self):
        if "date" not in self.table.columns:
            return

        if "description" not in self.table.columns:
            self.table["date"] = infer_and_fix_dates(self.table)
            return
        self._classify_transactions_via_tuned_bert()
        # I noticed like half of them are uncategorized but the LLMs are fully capable of classifying them - I would train a stupid model to make this faster - using a tiny fine tuned
        # bert is good but not enough. i think it can be better but time limited project so will eat the cost of APIs.
        self._classify_transactions()

        self.table["date"] = infer_and_fix_dates(self.table)
