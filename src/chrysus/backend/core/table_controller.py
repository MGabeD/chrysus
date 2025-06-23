from chrysus.backend.core.table_extractor import TableExtractor
from pathlib import Path
from chrysus.backend.core.informed_table import InformedTable


class TableController:

    def __init__(self, table_extractor: TableExtractor):
        self.tables = []
        self.table_extractor = table_extractor

    def extract_tables_from_pdf_and_add_to_self(self, pdf_path: Path):
        new_tables = self.table_extractor.extract(pdf_path)
        for table in new_tables:
            informed_table = InformedTable(table['table'], table['user_information'], pdf_path)

            self.tables.append(informed_table)

    
    

        

    
        
