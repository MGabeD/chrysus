import pdfplumber
import pytesseract
import re
import json
from typing import List, Dict, Any, Union
from chrysus.utils.logger import get_logger
from chrysus.backend.core.table_extractor import TableExtractor
from pathlib import Path
from langchain_core.language_models import BaseLanguageModel
from chrysus.backend.core.available_models import gemini_2, gemini_2_5
from concurrent.futures import ThreadPoolExecutor, as_completed

# TODO: I should prob switch to using layoutparser instead of pytesseract. I want to be able to preserve the layout for the model
# to be able to make better inferences... lets leave this for now and come back to it later

logger = get_logger(__name__)


class LLMExtractor(TableExtractor):
    """
    LLM-based table extractor that extracts tables from raw text using Google's Gemini models.
    This class focuses purely on text-based table extraction without OCR or PDF parsing.
    """
    
    def __init__(self, table_extractor_model: BaseLanguageModel = gemini_2_5, table_description_model: BaseLanguageModel = gemini_2, user_information_model: BaseLanguageModel = gemini_2):
        """Initialize the LLM extractor with Gemini models."""
        self.table_extractor_model = table_extractor_model
        self.table_description_model = table_description_model
        self.user_information_model = user_information_model

    def extract(self, pdf_path: Path):
        all_text = self._extract_text_from_pdf(pdf_path)
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Run user info and table description in parallel
            fut_user = executor.submit(self._extract_user_information_from_text, all_text)
            fut_tables = executor.submit(self._describe_tables_in_text, all_text)
            user_info = fut_user.result()
            tables_info = fut_tables.result()
        if not tables_info:
            main_table = self._extract_single_table_via_llm(all_text, "main")
            if self._is_valid_table(main_table):
                return [{'table': main_table, 'blurb': 'main table', 'user_information': user_info}]
            return []
        # Run table extractions in parallel
        results = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {
                executor.submit(self._extract_single_table_via_llm, all_text, table_info): table_info
                for table_info in tables_info
            }
            for future in as_completed(futures):
                table_info = futures[future]
                table = future.result()
                if self._is_valid_table(table):
                    results.append({
                        'table': table,
                        'desc': table_info.get('blurb', 'main table'),
                        'table_number': table_info.get('table_number', -1),
                        'user_information': user_info,
                    })
        return results
    
    def sequential_extract(self, pdf_path: Path) -> List[Dict[str, List[List]]]:
        """
        Extract tables from a PDF object by extracting text and then using LLM to parse tables.
        
        Args:
            pdf_object: The PDF document object (expected to have text extraction capability)

        Returns:
            List[Dict[str, List[List]]]: A list of dictionaries where each dictionary
            represents a table. The dictionary should contain the table data as a list of lists. Other 
            keys can be added to store other data about the table where helpful.
        """
        all_text = self._extract_text_from_pdf(pdf_path)
        llm_tables = self._extract_tables_from_text(all_text)
        summary_of_user_information = self._extract_user_information_from_text(all_text)
        logger.info(f"LLM extracted {len(llm_tables)} tables")
        for i in llm_tables:
            i['user_information'] = summary_of_user_information
        return llm_tables

    def _extract_text_via_pdfplumber(self, pdf_path: Path) -> str:
        all_text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                all_text += text + "\n"
        return all_text

    def _extract_text_via_ocr(self, pdf_path: Path) -> str:
        ocr_text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                pil_img = page.to_image(resolution=300).original
                ocr_text += pytesseract.image_to_string(pil_img) + "\n"
        return ocr_text

    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        all_text = self._extract_text_via_pdfplumber(pdf_path)
        if not all_text:
            logger.warning("No text extracted from PDF")
        if len(all_text.split()) < 100:
            logger.warning("Not enough text present in the PDF - running OCR")
            all_text = self._extract_text_via_ocr(pdf_path)
        return all_text
    
    def _extract_tables_from_text(self, text: str) -> List[Dict[str, List[List]]]:
        tables_info = self._describe_tables_in_text(text)
        if not tables_info:
            main_table = self._extract_single_table_via_llm(text, "main")
            if self._is_valid_table(main_table):
                return [{'table': main_table, 'blurb': 'main table'}]
            return []
        logger.info(f"LLM extracted {len(tables_info)} tables")
        results = []
        for table_info in tables_info:
            logger.info(f"Extracting table {table_info.get('table_number', -1)}")
            table = self._extract_single_table_via_llm(text, table_info)
            logger.info(f"Extracting table {table_info.get('table_number', -1)}")
            if self._is_valid_table(table):
                results.append({
                    'table': table,
                    'blurb': table_info.get('blurb', 'main table'),
                    'table_number': table_info.get('table_number', -1),
                })
            else:
                logger.warning(f"LLM extracted table {table_info.get('table_number', -1)} is not valid")
        return results
    
    def _extract_user_information_from_text(self, text: str) -> Dict[str, Any]:
        prompt = f"""
<task>
You are given text extracted from a PDF. Identify all of the user informationpresent in the text.
You must try your best to extract the user information, return:
- Name of the account holder
- Account number
- Account type
- Balance at the start of the period
- Balance at the end of the period
- Other relevant information a person would want to know when judging whether to give the account a loan
Respond as a JSON object, inside the XML tag, using only lowercase letters like:
<user_information>
{{"name": "...", "account_number": "...", "account_type": "...", "balance_start": "...", "balance_end": "...", "...": "..."}}
</user_information>
for unfound information, return "".
</task>
<input>
{text}
</input>
<output>
<user_information>
{"{...}"}
</user_information>
</output>
"""
        try:
            response = self.user_information_model.invoke(prompt)
            match = re.search(r"<user_information>(.*?)</user_information>", response.content, re.DOTALL)
            if not match:
                return {}
            return json.loads(match.group(1))
        except Exception as e:
            logger.error(f"Error extracting user information from text: {e}")
            return {}

    def _describe_tables_in_text(self, text: str) -> List[Dict[str, Any]]:
        prompt = f"""
<task>
You are given text extracted from a PDF. Identify all tables relevant to the account transactions or balances present in the text.
For each table, return:
- Table number (starting from 1)
- A short description ("blurb") of what the table contains. This should clearly describe the contents of the table, and thus also how it is different from the other tables present in the text.
- The first phrase/row of the table, to help us locate it later
Respond as a JSON list, inside the XML tag, like:
<tables>
[
  {{"table_number": 1, "blurb": "...", "start_phrase": "..."}},
  {{"table_number": 2, "blurb": "...", "start_phrase": "..."}}
]
</tables>
</task>
<input>
{text}
</input>
<output>
<tables>
[ ... ]
</tables>
</output>
"""
        try:
            response = self.table_description_model.invoke(prompt)
            match = re.search(r"<tables>(.*?)</tables>", response.content, re.DOTALL)
            if not match:
                return []
            
            table_list = json.loads(match.group(1))
            return table_list
        except Exception as e:
            logger.error(f"Error describing tables in text: {e}")
            return []
    
    def _extract_single_table_via_llm(self, text: str, description_blurb: Dict[str, Any] = {"blurb": "main table"}) -> Union[List[List[Any]], None]:
        blurb_as_text = f"table with the following information: {' '.join(f'{k}: {v}' for k, v in description_blurb.items())}"
        prompt = f"""
<task>
You are given text extracted from a PDF. Your job is to extract the {blurb_as_text} in the text.
- Return ONLY the table data, using JSON (list of lists).
- The first list must be the column headers.
- If the table splits possitive and negative transactions, unify the columns into a single column with expenditures as a negative and incoming funds as a possitive. 
- If applicable, determine the tracking column for the transactions, this will either be something like amount, total, or balance. Rename the column to "transaction_amount" if it is tracking the size of the transaction. Otherwise, if it is tracking the account balance, rename the column to balance.
- Rename where it makes sense: the column describing the date to "date", balance to "balance", the counterparty of the transaction to "description", all other columns should retain the same name.
- The counterparty or description of column can commonly be found with names like Description, Particulars, Transaction Description, etc.,
- Do not include any commentary or explanation.
- You MUST respond strictly within the provided XML tags. If you do not, the caller will not be able to parse your response.
We require the "<json_table>" tag to be present in your response.
</task>
<input>
{text}
</input>
<output>
<json_table>
{'{"table":[[header1, header2, ...], [row1col1, row1col2, ...], ...]}'}
</json_table>
</output>
"""
        try:
            response = self.table_extractor_model.invoke(prompt)
            match = re.search(r"<json_table>(.*?)</json_table>", response.content, re.DOTALL)
            if not match:
                return None
            
            table_json = json.loads(match.group(1))
            if not self._is_valid_table(table_json.get('table')):
                logger.warning(f"LLM extracted table is not valid: {table_json.get('table')}")
                return None
            return table_json.get('table')
        except Exception as e:
            logger.error(f"Error extracting table via LLM: {e}")
            return None
    