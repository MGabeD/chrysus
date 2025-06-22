import pdfplumber
import pytesseract
from PIL import Image
import re
import json
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from chryseos.utils.logger import get_logger
from chryseos import resolve_component_dirs_path

# TODO: I should prob switch to using layoutparser instead of pytesseract. I want to be able to preserve the layout for the model
# to be able to make better inferences... lets leave this for now and come back to it later


DATA_DIR = resolve_component_dirs_path("sample_data")
logger = get_logger(__name__)


gemini_2_flash = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
)


gemini_2_5 = ChatGoogleGenerativeAI(
    model="gemini-2.5",
    temperature=0,
    thinking_config={"budget": 1024}
)


def is_valid_table(table):
    if not table or not isinstance(table, list) or len(table) < 2:
        return False
    row_lens = [len(row) for row in table if isinstance(row, list)]
    if len(set(row_lens)) > 1:
        return False
    return True


def describe_tables_in_text(text):
    """
    Uses the LLM to analyze the input text and return a list of descriptions for each table detected.
    Returns a list of dicts: [{ 'table_number': 1, 'blurb': '...', 'start_phrase': '...' }, ...]
    """
    prompt = f"""
<task>
You are given text extracted from a PDF. Identify all tables present in the text.
For each table, return:
- Table number (starting from 1)
- A one-sentence description ("blurb") of what the table contains
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
    response = llm.invoke(prompt)
    match = re.search(r"<tables>(.*?)</tables>", response.content, re.DOTALL)
    if not match:
        return []
    try:
        table_list = json.loads(match.group(1))
    except Exception:
        return []
    return table_list


def extract_table_via_llm(text, description_blurb="main"):
    """
    Extracts a single table from text given a brief description or context ("main", or something from describe_tables_in_text).
    """
    prompt = f"""
<task>
You are given text extracted from a PDF. Your job is to extract the {description_blurb} table in the text.
- Return ONLY the table data, using JSON (list of lists).
- The first list must be the column headers.
- Do not include any commentary or explanation.
- Respond strictly within the provided XML tags.
</task>
<input>
{text}
</input>
<output>
<json_table>
[[header1, header2, ...], [row1col1, row1col2, ...], ...]
</json_table>
</output>
"""
    response = llm.invoke(prompt)
    match = re.search(r"<json_table>(.*?)</json_table>", response.content, re.DOTALL)
    if not match:
        return None
    try:
        table_json = json.loads(match.group(1))
    except Exception:
        return None
    return table_json if is_valid_table(table_json) else None


def extract_all_tables_from_text(text):
    """
    Detects all tables in the input text and extracts each one with a blurb.
    If only one table, just returns it.
    Returns: list of { 'blurb': ..., 'table': ... }
    """
    tables_info = describe_tables_in_text(text)
    if not tables_info:
        # fallback: try to extract one main table
        main_table = extract_table_via_llm(text)
        if is_valid_table(main_table):
            return [{'blurb': 'main', 'table': main_table}]
        return []
    results = []
    for tinfo in tables_info:
        desc = tinfo.get('blurb', 'main')
        table = extract_table_via_llm(text, description_blurb=desc)
        if is_valid_table(table):
            results.append({'blurb': desc, 'table': table})
    return results


def extract_text_via_ocr(pdf_path):
    ocr_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pil_img = page.to_image(resolution=300).original
            ocr_text += pytesseract.image_to_string(pil_img) + "\n"
    return ocr_text


def extract_text_via_pdfplumber(pdf_path):
    all_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            all_text += text + "\n"
    return all_text


def extract_table_via_pdfplumber(pdf_path):
    found_table = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                found_table.extend(table)
    return found_table


def extract_table_ensure_target(pdf_path):
    all_text = extract_text_via_pdfplumber(pdf_path)
    found_table = extract_table_via_pdfplumber(pdf_path)
    table_word_length = sum(len(str(cell).split()) for row in found_table for cell in row) if found_table else 0
    all_text_word_length = len(all_text.split())
    # MARK: this is arbitrary - making sure we actually got some real text - if not then we do OCR
    if all_text_word_length < 100:
        logger.warning("Not enough text present in the PDF - running OCR")
        all_text = extract_text_via_ocr(pdf_path)
        all_text_word_length = len(all_text.split())
    # MARK: this is abritrary - guarding against grabbing extra garbage tables - if we are not getting the main one then we 
    # clearly have an issue - this is MVP logic for sure but its better for safety
    if is_valid_table(found_table) and table_word_length > all_text_word_length / 10:
        return found_table
    llm_table = extract_table_via_llm(all_text)
    if is_valid_table(llm_table):
        return llm_table
    logger.error("Table extraction failed after both attempts.")
    return None

def robust_extract_table(pdf_path):
    return extract_table_ensure_target(pdf_path)


if __name__ == "__main__":
    # robust_extract_table(DATA_DIR / "data_sample_1.pdf")
    # robust_extract_table(DATA_DIR / "data_sample_2.pdf")
    # robust_extract_table(DATA_DIR / "data_sample_3.pdf")
    robust_extract_table(DATA_DIR / "data_sample_4.pdf")
