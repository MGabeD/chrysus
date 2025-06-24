from typing import Optional, List
from chrysus.backend.core.informed_table import InformedTable, clean_for_json
import pandas as pd
from chrysus.utils.logger import get_logger
from chrysus.backend.core.available_models import gemini_2_5
import json
import re


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
            return clean_for_json(self.transaction_table.insights['transaction_features'])
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
        for index, table in enumerate(self.descriptive_tables):
            df = table.table.copy()
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Get the table title from user_information description, or use default
            table_title = table.user_information.get('title', f'Descriptive Table {index + 1}')
            
            table_data = {
                'title': table_title,
                'data': clean_for_json(df.to_dict(orient="records"))
            }
            
            tables_json.append(table_data)
        
        return tables_json
        
    def get_recommendations(self):
        base_insights = self.get_base_insights()
        descriptive_tables = self.get_descriptive_tables_json()
        transaction_table = self.get_transaction_table_json()

        if not base_insights or not transaction_table:
            return {"error": "Insufficient data for recommendation."}

        # The clean_for_json function might have already converted these to strings
        # but we ensure they are proper JSON strings for the prompt.
        base_insights_json = json.dumps(base_insights, indent=2)
        descriptive_tables_json = json.dumps(descriptive_tables, indent=2)
        transaction_table_json = json.dumps(transaction_table, indent=2)

        prompt = f"""
<task>
You are a senior loan officer. Your task is to analyze a client's financial data to determine if they are a suitable candidate for a small business style loan.
You must provide a clear recommendation: "ACCEPT" or "REJECT" or "DEFER".
Your analysis must be comprehensive, covering the client's financial strengths and weaknesses.
You must back up your claims with specific examples and figures from their transaction history.

1.  **Primary Data**: Use the 'Base Insights' as your primary source for high-level statistics like income, expenses, and spending habits.
2.  **Supplementary Data**: Use the 'Descriptive Tables' to understand other financial aspects, like summaries of different accounts or assets.
3.  **Evidence**: Use the 'Transaction Table' to find concrete examples that support your reasoning.
4.  **Structure your response**:
    -   **Recommendation**: Start with "ACCEPT" or "REJECT".
    -   **Reasoning**: A concise paragraph explaining your decision.
    -   **Strengths**: A bulleted list of the client's financial strengths.
    -   **Weaknesses**: A bulleted list of the client's financial weaknesses.
    -   **Evidence**: A list of specific transactions or data points that justify your conclusion.

You MUST respond strictly within the provided XML tags.
</task>

<client_data>

<base_insights>
{base_insights_json}
</base_insights>

<descriptive_tables>
{descriptive_tables_json}
</descriptive_tables>

<transaction_table>
{transaction_table_json}
</transaction_table>

</client_data>

<output>
<recommendation>
...
</recommendation>
</output>
"""
        try:
            llm = gemini_2_5
            response = llm.invoke(prompt)
            
            # Parse all the XML components from the response
            recommendation_match = re.search(r"<recommendation>(.*?)</recommendation>", response.content, re.DOTALL)
            reasoning_match = re.search(r"<reasoning>(.*?)</reasoning>", response.content, re.DOTALL)
            strengths_match = re.search(r"<strengths>(.*?)</strengths>", response.content, re.DOTALL)
            weaknesses_match = re.search(r"<weaknesses>(.*?)</weaknesses>", response.content, re.DOTALL)
            evidence_match = re.search(r"<evidence>(.*?)</evidence>", response.content, re.DOTALL)

            if recommendation_match:
                result = {
                    "recommendation": recommendation_match.group(1).strip(),
                    "reasoning": reasoning_match.group(1).strip() if reasoning_match else "",
                    "strengths": strengths_match.group(1).strip() if strengths_match else "",
                    "weaknesses": weaknesses_match.group(1).strip() if weaknesses_match else "",
                    "evidence": evidence_match.group(1).strip() if evidence_match else ""
                }
                return result
            else:
                logger.error(f"Could not parse recommendation from LLM response: {response.content}")
                return {"error": "Failed to parse recommendation from model response."}
        except Exception as e:
            logger.error(f"Error getting recommendation: {e}")
            return {"error": "An exception occurred while generating the recommendation."}
