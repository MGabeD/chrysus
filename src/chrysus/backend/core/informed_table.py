import copy
import re
import json
from dateutil import parser
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import List, Dict, Any, Optional, Union
import pandas as pd
from pathlib import Path
from langchain_core.language_models import BaseLanguageModel
from chrysus.backend.core.available_models import gemini_2, gemini_2_5
from chrysus.utils.logger import get_logger


logger = get_logger(__name__)

# kuro-08/bert-transaction-categorization
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


def user_information_union(left: dict, right: dict) -> dict:
    union_dict = copy.deepcopy(left)
    for k,v in right.items():
        if k not in union_dict:
            union_dict[k] = v
        else:
            if isinstance(union_dict[k], set):
                union_dict[k].add(v)
            else:
                union_dict[k] = set(union_dict[k]).add(v)
    return union_dict


class InformedTable:

    _classifier_pipe: Optional[pipeline] = None

    def __init__(self, table: List[List[Any]], user_information: Dict[str, Any], pdf_path: Union[Path, str], resolver_llm: BaseLanguageModel = gemini_2_5):
        for i in range(len(table[0])):
            table[0][i] = table[0][i].lower()

        self.table = pd.DataFrame(table[1:], columns=table[0])
        self.user_information = user_information
        self.insights = []
        self.transformation_history = []
        self.pdf_path = {str(pdf_path)}
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
row's "txn_category" cell. The txn_category column should be a generalized category
of a transaction. For example, "food", "leisure", "utilities", "salary", "rent", "transport", "health", etc.
Some transactions are much more important to correctly categorize, like any loans, mortgages, credit card payments, and ANY debt.
Never give a category that is too specific Ex: Gym membership or Bank fees should be "health" or "utilities" 
No commentary. You MUST respond strictly within the provided XML tags. If you do not, the caller will not be able to parse your response.
We require the "<json_table>" tag to be present in your response.
</task>
<input>
{payload}
</input>
<output>
<json_table>
{{"table":[["index","date","description","transaction_amount","balance","txn_category"], ...]}}
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

    def _convert_balance_to_transaction_amount(self):
        """
        Convert balance column to transaction amounts by calculating differences between consecutive balances.
        The transaction amount for row i is: balance[i] - balance[i-1]
        """
        if "balance" not in self.table.columns:
            logger.warning("No 'balance' column found for transaction amount conversion")
            return
        try:
            self.table["balance"] = pd.to_numeric(self.table["balance"], errors="coerce")
        except Exception as e:
            logger.error(f"Failed to convert balance column to numeric: {e}")
            return
            
        self.table["transaction_amount"] = self.table["balance"].diff()
        self.transformation_history.append(
            {
                "step": "balance_to_transaction_amount_conversion",
                "rows": len(self.table),
                "non_null_transaction_amounts": self.table["transaction_amount"].notna().sum()
            }
        )
        logger.info(f"Converted balance to transaction amount for {len(self.table)} rows")

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

        # Now I need to figure out if the data can be turned into a standard table for actual work to be done. I need to talk to he LLM and get it to do some simple work
        # I think I want a standardized Date, Tag, Delta

        if "transaction_amount" not in self.table.columns:
            self._convert_balance_to_transaction_amount()
        # As of here we are forcing all data passing here to have a date, description, txn_category, and transaction_amount
        # This is the base enforced interface for the table. Now we need to figure out how to identify if these are the same users since we don't have ids.
        self.table = self.table.rename(columns={'txn_category': 'tag'})

    @staticmethod
    def unify_tables(table1: "InformedTable", table2: "InformedTable") -> "InformedTable":
        """
        Unifies two InformedTable objects into a new InformedTable:
        - Columns are unioned and missing values filled with NA.
        - Fails if either is a transaction table (is_transaction_table True).
        - resolver_llm is inherited from table1.
        - insights is a distinct union of both.
        - pdf_path is union of both as set.
        Returns a new InformedTable instance.
        """
        if table1.is_transaction_table or table2.is_transaction_table:
            raise ValueError("Cannot unify tables when either is a transaction table.")

        unified_df = pd.concat([table1.table, table2.table], ignore_index=True)
        unified_df = unified_df.drop_duplicates()

        insights = list({*table1.insights, *table2.insights})
        pdf_paths = table1.pdf_path | table2.pdf_path
        user_information = user_information_union(table1.user_information, table2.user_information)

        new_informed_table = InformedTable(
            table= unified_df.sort_values(by="date", ascending=True, na_position="last"),
            user_information=user_information,
            pdf_path=pdf_paths,
            resolver_llm=table1.resolver_llm
        )
        new_informed_table.insights = insights
        return new_informed_table

    def extract_transaction_features(self):
        if not self.is_transaction_table:
            logger.info("Feature extraction only valid for transaction tables.")
            return

        df = self.table.copy()
        features = {}

        if not pd.api.types.is_datetime64_any_dtype(df["date"]):
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        desc_counts = df["description"].value_counts()
        frequent_descs = desc_counts[desc_counts > 3].index.tolist()
        desc_grouped = (
            df[df["description"].isin(frequent_descs)]
            .groupby("description")["transaction_amount"]
            .agg(["mean", "max", "min", "sum", "std", "count"])
            .reset_index()
        )
        features["frequent_descriptions"] = desc_grouped.to_dict(orient="records")

        tag_grouped = (
            df.groupby("tag")["transaction_amount"]
            .agg(["mean", "max", "min", "sum", "std", "count"])
            .reset_index()
        )
        features["tags"] = tag_grouped.to_dict(orient="records")

        df["month"] = df["date"].dt.to_period("M")
        monthly_grouped = (
            df.groupby("month")["transaction_amount"]
            .agg(["mean", "max", "min", "sum", "std", "count"])
            .reset_index()
        )

        monthly_grouped["month"] = monthly_grouped["month"].astype(str)
        features["monthly"] = monthly_grouped.to_dict(orient="records")

        df["week"] = df["date"].dt.to_period("W")
        weekly_grouped = (
            df.groupby("week")["transaction_amount"]
            .agg(["mean", "max", "min", "sum", "std", "count"])
            .reset_index()
        )
        weekly_grouped["week"] = weekly_grouped["week"].astype(str)
        features["weekly"] = weekly_grouped.to_dict(orient="records")

        self.insights.append({"transaction_features": features})
        return features