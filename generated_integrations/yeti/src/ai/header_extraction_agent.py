"""
header_extraction_agent.py

Extracts source fields from customer files.

Supports:
- CSV headers
- JSON keys
"""

import json
from pathlib import Path

import pandas as pd


class HeaderExtractionAgent:
    """
    Extract source field names from supported file types.
    """

    def extract_headers(self, file_path: str) -> list[str]:
        extension = Path(file_path).suffix.lower()

        if extension == ".csv":
            return self.extract_csv_headers(file_path)

        if extension == ".json":
            return self.extract_json_headers(file_path)

        raise ValueError(
            f"Unsupported file type for header extraction: {extension}"
        )

    def extract_csv_headers(self, file_path: str) -> list[str]:
        df = pd.read_csv(file_path, nrows=0)
        return list(df.columns)

    def extract_json_headers(self, file_path: str) -> list[str]:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list) and data:
            first_record = data[0]

            if isinstance(first_record, dict):
                return list(first_record.keys())

        if isinstance(data, dict):
            if "orders" in data and isinstance(data["orders"], list) and data["orders"]:
                first_record = data["orders"][0]

                if isinstance(first_record, dict):
                    return list(first_record.keys())

            return list(data.keys())

        raise ValueError(
            "Could not extract headers from JSON file."
        )