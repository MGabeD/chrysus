from typing import Optional
from chrysus.backend.core.informed_table import InformedTable

class AccountHolder:

    def __init__(self, name: str = None, account_ids: set = set()):
        self.name = name
        self.account_ids = set(account_ids)
        self.descriptive_tables = []
        self.transaction_table: Optional[InformedTable] = None

    def add_descriptive_table(self, table: InformedTable):
        self.descriptive_tables.append(table)

    def add_transaction_table(self, table: InformedTable):
        if self.transaction_table is not None:
            self.transaction_table = InformedTable.unify_tables(self.transaction_table, table)
        else:
            self.transaction_table = table

    def add_table(self, table: InformedTable):
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
            return self.transaction_table.insights
        else:
            return self.transaction_table.extract_transaction_features()
        
            
