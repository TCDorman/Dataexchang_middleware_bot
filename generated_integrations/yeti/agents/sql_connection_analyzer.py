import json
from pathlib import Path

from src.connectors.sql_connector import SqlConnector


def analyze_sql_connection_string(connection_string: str) -> dict:
    connector = SqlConnector()

    result = connector.analyze_connection_string(
        connection_string=connection_string,
    )

    output_folder = Path("generated_integrations") / "sql_connection_analysis"
    output_folder.mkdir(parents=True, exist_ok=True)

    output_path = output_folder / "sql_analysis_result.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=4)

    result["output_path"] = str(output_path)

    return result