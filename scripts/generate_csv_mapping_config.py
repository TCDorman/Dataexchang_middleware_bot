import sys
from pathlib import Path
import json
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.mapping_agent import suggest_wms_mappings


def generate_csv_mapping_config(header_file, line_file, output_path):
    header_df = pd.read_csv(header_file)
    line_df = pd.read_csv(line_file)

    header_fields = list(header_df.columns)
    line_fields = list(line_df.columns)

    all_fields = header_fields + line_fields

    result = suggest_wms_mappings(all_fields)

    config = {
        "header_mappings": {},
        "line_mappings": {}
    }

    for mapping in result.mappings:
        entry = {
            "internal_field": mapping.internal_field,
            "wms_field": mapping.suggested_wms_field,
            "confidence": mapping.confidence,
            "reason": mapping.reason,
        }

        if mapping.source_field in header_fields:
            config["header_mappings"][mapping.source_field] = entry

        if mapping.source_field in line_fields:
            config["line_mappings"][mapping.source_field] = entry

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=4)

    print(f"Generated CSV mapping config: {output_file}")


if __name__ == "__main__":
    generate_csv_mapping_config(
        "data/sample_files/test_ui_headers.csv",
        "data/sample_files/test_ui_lines.csv",
        "configs/mappings/csv_mapping_config.json",
    )