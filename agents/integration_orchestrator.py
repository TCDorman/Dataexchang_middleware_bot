import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools.tool_registry import TOOLS


def detect_source_type(file_paths: list[str]) -> str:
    extensions = [Path(path).suffix.lower() for path in file_paths]

    if len(file_paths) == 2 and all(ext == ".csv" for ext in extensions):
        return "csv"

    if len(file_paths) == 1 and extensions[0] == ".json":
        return "json"

    if len(file_paths) == 1 and extensions[0] == ".xml":
        return "xml"

    raise ValueError(f"Unsupported input files: {file_paths}")


def run_integration(file_paths: list[str]):
    source_type = detect_source_type(file_paths)

    if source_type == "csv":
        tool = TOOLS["convert_csv_to_wms_xml"]

        return tool(
            file_paths[0],
            file_paths[1],
            "data/output/orchestrated_csv_orders.xml",
        )

    if source_type == "json":
        tool = TOOLS["convert_json_to_wms_xml"]

        return tool(
            file_paths[0],
            "data/output/orchestrated_json_orders.xml",
        )

    if source_type == "xml":
        tool = TOOLS["convert_xml_to_wms_xml"]

        return tool(
            file_paths[0],
            "configs/mappings/xml_mapping_config.json",
        )


if __name__ == "__main__":
    result = run_integration(
        [
            "data/sample_files/CFG-IMP-ORDINI.xml",
        ]
    )

    print(result)