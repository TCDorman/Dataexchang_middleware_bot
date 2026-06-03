"""
parser_factory.py

Determines which parser should be used based on the
input file type.
"""

from pathlib import Path

from src.parsing.csv_order_parser import CsvOrderParser


class ParserFactory:
    """
    Creates the appropriate parser for a file type.
    """

    @staticmethod
    def get_parser(file_path: str):
        """
        Determine which parser to use.

        Args:
            file_path: Input file path.

        Returns:
            Parser instance.
        """

        extension = Path(file_path).suffix.lower()

        if extension == ".csv":
            return CsvOrderParser()

        raise ValueError(
            f"Unsupported file type: {extension}"
        )