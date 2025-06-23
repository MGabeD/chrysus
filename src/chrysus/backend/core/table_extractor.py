from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any


class TableExtractor(ABC):
    """
    Abstract base class for table extraction from PDF documents.
    
    This class defines the interface that all table extractors must implement.
    The extract method should parse PDF documents and return structured table data.
    """
    
    def _is_valid_table(self, table: List[List[Any]]) -> bool:
        """
        Check if a table is valid.
        """
        if not table or not isinstance(table, list) or len(table) < 2:
            return False
        row_lens = [len(row) for row in table if isinstance(row, list)]
        if len(set(row_lens)) > 1:
            return False
        return True
        

    @abstractmethod
    def extract(self, pdf_path: Path) -> List[Dict[str, List[List]]]:
        """
        Extract tables from a PDF document.
        
        Args:
            pdf_path: The path to the PDF document to extract tables from.
        
        Returns:
            List[Dict[str, List[List]]]: A list of dictionaries where each dictionary
            represents a table. The dictionary should contain the table data as a list of lists. Other 
            keys can be added to store other data about the table where helpful.
            
        Raises:
            NotImplementedError: Must be implemented by concrete subclasses.
        """
        pass
