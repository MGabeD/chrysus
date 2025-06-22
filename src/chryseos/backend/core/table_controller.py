from chryseos.backend.core.table_extractor import TableExtractor
from pathlib import Path


class TableController:

    def __init__(self, table_extractor: TableExtractor):
        self.tables = []
        self.table_extractor = table_extractor

    def extract_table_from_pdf_and_add_to_self(self, pdf_path: Path):
        self.tables.extend(self.table_extractor.extract(pdf_path))
