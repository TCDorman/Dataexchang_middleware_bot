import sys
from pathlib import Path
import json

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.mapping_agent import suggest_wms_mappings


def generate_mapping_config(source_fields: list[str], output_path: str):

    result = suggest_wms_mappings(source_fields)

    config = {}

    for mapping in result.mappings:
        config[mapping.source_field] = {
            "internal_field": mapping.internal_field,
            "wms_field": mapping.suggested_wms_field,
            "confidence": mapping.confidence,
            "reason": mapping.reason,
        }

    output_file = Path(output_path)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=4)

    return output_file


if __name__ == "__main__":

    sample_fields = [
    "po_num",
    "buyer",
    "fulfillment_mode",
    "po_ref",
    "part_no",
    "qty_requested",
]

    output_path = "configs/mappings/sample_mapping_config.json"

    generated_file = generate_mapping_config(
        sample_fields,
        output_path,
    )

    print(f"\nGenerated mapping config:\n{generated_file}")