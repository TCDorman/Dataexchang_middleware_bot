"""
mapping_confirmation_agent.py

Allows a user to confirm or override LLM-suggested field mappings.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def confirm_mapping_result(
    mapping_result: Dict[str, Any],
    output_path: str,
) -> Dict[str, Any]:
    field_mapping = mapping_result.get("field_mapping", {})
    mapping_confidence = mapping_result.get("mapping_confidence", {})
    mapping_notes = mapping_result.get("mapping_notes", {})

    confirmed_mapping = {}

    print("\nLLM FIELD MAPPING REVIEW")
    print("=" * 70)

    for internal_field, suggested_source_field in field_mapping.items():
        confidence = mapping_confidence.get(internal_field, 0)
        note = mapping_notes.get(internal_field, "")

        print(f"\nModula Field: {internal_field}")
        print(f"Suggested Customer Field: {suggested_source_field}")
        print(f"Confidence: {confidence}")
        print(f"Reason: {note}")

        choice = input("Accept this mapping? [Y/n/override]: ").strip().lower()

        if choice in ["", "y", "yes"]:
            confirmed_mapping[internal_field] = suggested_source_field

        elif choice in ["n", "no"]:
            confirmed_mapping[internal_field] = None

        elif choice in ["o", "override"]:
            new_field = input("Enter customer source field to use: ").strip()
            confirmed_mapping[internal_field] = new_field or None

        else:
            confirmed_mapping[internal_field] = suggested_source_field

    confirmed_result = {
        "status": "confirmed",
        "confirmed_at": datetime.now().isoformat(timespec="seconds"),
        "original_mapping_result": mapping_result,
        "confirmed_field_mapping": confirmed_mapping,
    }

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(confirmed_result, file, indent=4)

    return confirmed_result