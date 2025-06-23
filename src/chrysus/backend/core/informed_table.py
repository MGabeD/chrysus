from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import List, Dict, Any
import pandas as pd
from pathlib import Path
from langchain_core.language_models import BaseLanguageModel
from chrysus.backend.core.available_models import gemini_2


_MODEL_NAME = (
    "wanadzhar913/debertav3-finetuned-banking-transaction-classification-text-only"
)

class InformedTable:


    _classifier_pipe: "pipeline" | None = None

    def __init__(self, table: List[List[Any]], user_information: Dict[str, Any], pdf_path: Path):
        for i in range(len(table[0])):
            table[0][i] = table[0][i].lower()

        self.table = pd.DataFrame(table[1:], columns=table[0])
        self.user_information = user_information
        self.insights = []
        self.pdf_path = pdf_path
        self.is_transaction_table = False
        self.pre_process_insights()

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

    def pre_process_insights(self, model: BaseLanguageModel = gemini_2):
        if "description" not in self.table.columns:
            return

        self.is_transaction_table = True
        classifier = self._get_classifier()

        narratives = self.table["description"].fillna("").astype(str).tolist()
        raw_preds = classifier(narratives)
        labels = [
            p[0]["label"] if isinstance(p, list) else p["label"]
            for p in raw_preds
        ]
        self.table["txn_category"] = labels
        # this is only for debugging
        self.insights.append(
            {
                "step": "txn_classification",
                "model": _MODEL_NAME,
                "rows": len(self.table),
            }
        ) 



            


