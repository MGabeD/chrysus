from chrysus.backend.core.table_controller import TableController
from pathlib import Path
from chrysus import resolve_component_dirs_path


TEST_PDF_PATH = resolve_component_dirs_path("sample_data") 


def test_table_controller():
    table_controller = TableController()
    table_controller.extract_tables_from_pdf_and_add_to_self(TEST_PDF_PATH / "data_sample_1.pdf")
    for table in table_controller.tables:
        print(table.table.head(10))
        if {'description', 'date'}.issubset(table.table.columns):
            table.table.to_csv('foo.csv', index=False)

if __name__ == "__main__":
    test_table_controller()