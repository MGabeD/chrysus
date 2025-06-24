import copy
from chrysus.backend.core.table_extractor import TableExtractor
from pathlib import Path
from chrysus.backend.core.informed_table import InformedTable
from chrysus.backend.core.llm_extractor import LLMExtractor
from typing import Dict
from chrysus.backend.core.account_holder import AccountHolder
from chrysus.utils.logger import get_logger

logger = get_logger(__name__)

class AccountsController:

    def __init__(self, table_extractor: TableExtractor = LLMExtractor()):
        self.account_holder_map: Dict[str, AccountHolder] = {}
        self.table_extractor = table_extractor
        self.identifiers = {}

    def extract_tables_from_pdf_and_add_to_self(self, pdf_path: Path):
        new_tables = self.table_extractor.extract(pdf_path)
        cur_name = None
        stack_of_data = []
        account_numbers = set()
        for table in new_tables:
            cur_table = InformedTable(table['table'], copy.deepcopy(table['user_information']), pdf_path)
            cur_table.user_information['title'] = table.get('title', 'main table')
            if cur_name is None and cur_table.user_information.get("name", None) is not None:
                cur_name = cur_table.user_information.get("name", None)
            elif cur_name is None and cur_table.user_information.get("account_number", None) is not None:
                account_numbers.add(cur_table.user_information.get("account_number", None))
                cur_name = self.identifiers.get(cur_table.user_information.get("account_number", None), None) 
            if cur_name is not None:
                if self.account_holder_map.get(cur_name, None) is not None:
                    self.account_holder_map[cur_name].add_table(cur_table)
                else:
                    self.account_holder_map[cur_name] = AccountHolder(name=cur_name, account_ids=set([cur_table.user_information.get("account_number", None)]))
                    self.account_holder_map[cur_name].add_table(cur_table)
            else:
                stack_of_data.append(cur_table)
        if cur_name is None:
            logger.error(f"Found no name in {pdf_path}")
            return
        for table in stack_of_data:
            self.account_holder_map[cur_name].add_table(cur_table)
            for i in account_numbers:
                self.identifiers[i] = cur_name
    
    def get_account_holder(self, name: str = None, account_number: str = None) -> AccountHolder:
        if name is not None:
            return self.account_holder_map.get(name, None)
        elif account_number is not None:
            return self.account_holder_map.get(self.identifiers.get(account_number, None), None)
        else:
            return None
        