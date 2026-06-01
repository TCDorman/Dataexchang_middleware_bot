import sys
from pathlib import Path
import json

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.mapping_agent import suggest_wms_mappings


def generate_mapping_from_fields(fields: list[str]):
    mapping_result = suggest_wms_mappings(fields)

    mappings = []

    for mapping in mapping_result.mappings:
        mappings.append(
            {
                "source_field": mapping.source_field,
                "internal_field": mapping.internal_field,
                "wms_field": mapping.suggested_wms_field,
                "confidence": mapping.confidence,
                "reason": mapping.reason,
            }
        )

    return {
        "status": "success",
        "mappings": mappings,
    }


def save_mapping_config(mapping_result: dict, output_path: str):
    config = {}

    for mapping in mapping_result["mappings"]:
        config[mapping["source_field"]] = {
            "internal_field": mapping["internal_field"],
            "wms_field": mapping["wms_field"],
            "confidence": mapping["confidence"],
            "reason": mapping["reason"],
        }

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=4)

    return {
        "status": "success",
        "output_path": str(output_file),
    }