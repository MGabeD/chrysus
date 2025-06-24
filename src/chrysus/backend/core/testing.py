from chrysus.backend.core.accounts_controller import AccountsController
from pathlib import Path
from chrysus import resolve_component_dirs_path


TEST_PDF_PATH = resolve_component_dirs_path("sample_data") 


def test_table_controller():
    table_controller = AccountsController()
    # table_controller.extract_tables_from_pdf_and_add_to_self(TEST_PDF_PATH / "data_sample_1.pdf")
    table_controller.extract_tables_from_pdf_and_add_to_self(TEST_PDF_PATH / "data_sample_2.pdf")
    # table_controller.extract_tables_from_pdf_and_add_to_self(TEST_PDF_PATH / "data_sample_3.pdf")
    # table_controller.extract_tables_from_pdf_and_add_to_self(TEST_PDF_PATH / "data_sample_4.pdf")
    for name, account_holder in table_controller.account_holder_map.items():
        print(name)
        print(account_holder.get_base_insights())
        print(account_holder.get_transaction_table_json())
        print(account_holder.get_descriptive_tables_json())
        print(account_holder.get_recommendations())

if __name__ == "__main__":
    test_table_controller()