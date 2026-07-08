"""
sql_mapping_profile_generator.py

Generates a reusable SQL mapping profile from interpreted SQL schema results.
"""

import json
from pathlib import Path


def generate_sql_mapping_profile(
    interpretation_path: str,
    customer_name: str = "sql_customer",
) -> dict:
    path = Path(interpretation_path)

    if not path.exists():
        return {
            "status": "error",
            "message": f"Interpretation file not found: {interpretation_path}",
        }

    with open(path, "r", encoding="utf-8") as file:
        interpretation = json.load(file)

    mapping = interpretation.get("recommended_modula_mapping", {})

    safe_customer_name = customer_name.strip().lower().replace(" ", "_")

    profile = {
        "customer_name": customer_name,
        "source_type": "sql",
        "target_system": "Modula WMS",
        "profile_type": "sql_mapping_profile",
        "header_table": _get_best_table(
            interpretation,
            "possible_order_header_tables",
        ),
        "line_table": _get_best_table(
            interpretation,
            "possible_order_line_tables",
        ),
        "field_mappings": mapping,
        "notes": [
            "Generated automatically from SQL schema interpretation.",
            "Review table and column mappings before using in production.",
        ],
    }

    output_folder = Path("configs") / "customers"
    output_folder.mkdir(parents=True, exist_ok=True)

    output_path = output_folder / f"{safe_customer_name}_sql_profile.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(profile, file, indent=4)

    return {
        "status": "success",
        "message": "SQL mapping profile generated successfully.",
        "output_path": str(output_path),
        "profile": profile,
    }


def _get_best_table(interpretation: dict, key: str) -> str | None:
    candidates = interpretation.get("summary", {}).get(key, [])

    if not candidates:
        return None

    return candidates[0].get("table_name")