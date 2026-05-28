import sys
from pathlib import Path
import json

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.mapping_agent import suggest_wms_mappings


def collect_json_fields(data, prefix=""):
    fields = set()

    if isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            fields.add(full_key)
            fields.update(collect_json_fields(value, full_key))

    elif isinstance(data, list):
        for item in data:
            fields.update(collect_json_fields(item, prefix))

    return fields


def generate_json_mapping_config(input_json_file, output_config_file):
    with open(input_json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    fields = sorted(collect_json_fields(data))

    result = suggest_wms_mappings(fields)

    config = {}

    for mapping in result.mappings:
        config[mapping.source_field] = {
            "internal_field": mapping.internal_field,
            "wms_field": mapping.suggested_wms_field,
            "confidence": mapping.confidence,
            "reason": mapping.reason,
        }

    output_path = Path(output_config_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=4)

    print(f"Generated JSON mapping config: {output_path}")


if __name__ == "__main__":
    generate_json_mapping_config(
        "data/sample_files/sample_rest_api_order_response.json",
        "configs/mappings/json_mapping_config.json",
    )