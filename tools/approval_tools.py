import json
from pathlib import Path


def save_approved_mapping(mapping_result: dict, output_path: str):
    approved_config = {}

    for mapping in mapping_result["mappings"]:
        approved_config[mapping["source_field"]] = {
            "internal_field": mapping["internal_field"],
            "wms_field": mapping["wms_field"],
            "confidence": mapping["confidence"],
            "reason": mapping["reason"],
            "approved": True,
        }

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(approved_config, file, indent=4)

    return {
        "status": "success",
        "approved_mapping_path": str(output_file),
    }


def load_approved_mapping(mapping_path: str):
    with open(mapping_path, "r", encoding="utf-8") as file:
        return json.load(file)