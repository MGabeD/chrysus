from typing import Optional, List
from chrysus.backend.core.informed_table import InformedTable, clean_for_json
import pandas as pd
from chrysus.utils.logger import get_logger


logger = get_logger(__name__)


class AccountHolder:

    def __init__(self, name: str = None, account_ids: set = set()):
        self.name = name
        self.account_ids = set(account_ids)
        self.descriptive_tables: List[InformedTable] = []
        self.transaction_table: Optional[InformedTable] = None

    def add_descriptive_table(self, table: InformedTable):
        self.descriptive_tables.append(table)

    def add_transaction_table(self, table: InformedTable):
        logger.info(f"Adding transaction table: {table.is_transaction_table}")
        if self.transaction_table is not None:
            self.transaction_table = InformedTable.unify_tables(self.transaction_table, table)
        else:
            self.transaction_table = table

    def add_table(self, table: InformedTable):
        logger.info(f"Adding table: {table.is_transaction_table}")
        if table.is_transaction_table:
            self.add_transaction_table(table)
        else:
            self.add_descriptive_table(table)
        if self.name is None:
            self.name = table.user_information.get("name", None)
        self.account_ids.add(table.user_information.get("account_number", None))

    def get_base_insights(self):
        if self.transaction_table is None:
            return None
        if len(self.transaction_table.insights) > 0:
            return clean_for_json(self.transaction_table.insights[0])
        else:
            return clean_for_json(self.transaction_table.extract_transaction_features())

    def get_transaction_table_json(self):
        if self.transaction_table is None:
            return None
        df = self.transaction_table.table.copy()
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        return clean_for_json(df.to_dict(orient="records"))

    def get_descriptive_tables_json(self):
        if not self.descriptive_tables:
            return []
        
        tables_json = []
        for table in self.descriptive_tables:
            df = table.table.copy()
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            tables_json.append(clean_for_json(df.to_dict(orient="records")))
        
        return tables_json
        
            
