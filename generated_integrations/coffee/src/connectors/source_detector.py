"""
source_detector.py

Detects the type of customer source provided to the integration agent.
"""

from pathlib import Path


class SourceDetector:
    """
    Detects source type from file path or source string.
    """

    @staticmethod
    def detect_source_type(source_path: str) -> str:
        source = source_path.strip()
        extension = Path(source).suffix.lower()

        # REST API URL
        if source.startswith("http://") or source.startswith("https://"):
            return "rest_api"

        # SQL / ODBC Connection String
        if (
            "Driver=" in source
            or "Server=" in source
            or "Database=" in source
        ):
            return "sql"

        # File-based integrations
        if extension == ".csv":
            return "csv"

        if extension == ".json":
            return "json"

        if extension == ".xml":
            return "xml"

        if extension in [".xlsx", ".xls"]:
            return "excel"

        return "unknown"