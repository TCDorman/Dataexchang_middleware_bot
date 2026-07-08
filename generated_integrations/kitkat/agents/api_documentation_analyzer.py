import json
from pathlib import Path

from src.connectors.rest_api_connector import RestApiConnector


def analyze_api_documentation_file(file_path: str) -> dict:
    path = Path(file_path)

    with open(path, "r", encoding="utf-8") as file:
        documentation_text = file.read()

    connector = RestApiConnector()

    result = connector.analyze_api_documentation(
        documentation_text=documentation_text,
    )

    output_folder = Path("generated_integrations") / "api_documentation_analysis"
    output_folder.mkdir(parents=True, exist_ok=True)

    output_path = output_folder / "api_analysis_result.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=4)

    result["output_path"] = str(output_path)

    return result