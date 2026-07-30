"""
parser_factory.py

Determines which parser should be used based on the
input file type.
"""

from pathlib import Path

from src.parsing.csv_order_parser import CsvOrderParser
from src.parsing.json_order_parser import JsonOrderParser
from src.parsing.xml_order_parser import XmlOrderParser


class ParserFactory:
    """
    Creates the appropriate parser for a file type.
    """

    @staticmethod
    def get_parser(file_path: str):
        extension = Path(file_path).suffix.lower()

        if extension == ".csv":
            return CsvOrderParser()

        if extension == ".json":
            return JsonOrderParser()

        if extension == ".xml":
            return XmlOrderParser()

        raise ValueError(
            f"Unsupported file type: {extension}"
        )