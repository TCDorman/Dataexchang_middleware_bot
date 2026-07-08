"""
sql_query_generator.py

Generates SQL SELECT queries from SQL mapping profiles.
"""

import json
from pathlib import Path


def generate_sql_query_from_profile(profile_path: str) -> dict:
    path = Path(profile_path)

    if not path.exists():
        return {
            "status": "error",
            "message": f"SQL profile not found: {profile_path}",
        }

    with open(path, "r", encoding="utf-8") as file:
        profile = json.load(file)

    header_table = profile.get("header_table")
    line_table = profile.get("line_table")
    field_mappings = profile.get("field_mappings", {})

    if not header_table or not line_table:
        return {
            "status": "error",
            "message": "Profile must include header_table and line_table.",
        }

    order_id_mapping = field_mappings.get("order_id")
    if not order_id_mapping:
        return {
            "status": "error",
            "message": "Profile must include order_id field mapping.",
        }

    join_column = order_id_mapping.get("column_name")

    select_parts = []

    for modula_field, mapping in field_mappings.items():
        if not mapping:
            continue

        table_name = mapping.get("table_name")
        column_name = mapping.get("column_name")

        if not table_name or not column_name:
            continue

        alias = "h" if table_name == header_table else "l"

        select_parts.append(f"    {alias}.{column_name} AS {column_name}")

    query = (
        "SELECT\n"
        + ",\n".join(select_parts)
        + f"\nFROM {header_table} h\n"
        + f"INNER JOIN {line_table} l\n"
        + f"    ON h.{join_column} = l.{join_column};"
    )

    output_path = (
        Path("generated_integrations")
        / "sql_connection_analysis"
        / "generated_sql_query.sql"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(query)

    return {
        "status": "success",
        "profile_path": str(path),
        "query": query,
        "output_path": str(output_path),
    }