"""
sql_schema_interpreter.py

Interprets SQL schema discovery results and suggests how tables/columns
could map into Modula WMS order import fields.
"""

import json
from pathlib import Path


def interpret_sql_schema(schema_result_path: str) -> dict:
    path = Path(schema_result_path)

    if not path.exists():
        return {
            "status": "error",
            "message": f"Schema result file not found: {schema_result_path}",
        }

    with open(path, "r", encoding="utf-8") as file:
        schema_result = json.load(file)

    tables = schema_result.get("tables", [])

    interpretation = {
        "status": "success",
        "source_type": "sql",
        "schema_result_path": str(path),
        "summary": {
            "tables_analyzed": len(tables),
            "possible_order_header_tables": [],
            "possible_order_line_tables": [],
        },
        "recommended_modula_mapping": {
            "order_id": None,
            "customer_name": None,
            "ship_to_name": None,
            "ship_to_address": None,
            "item": None,
            "quantity": None,
            "location": None,
        },
    }

    for table in tables:
        table_name = table.get("table_name", "")
        columns = table.get("columns", [])

        column_names = [
            column.get("column_name", "")
            for column in columns
            if isinstance(column, dict)
        ]

        table_score = _score_table(table_name, column_names)

        if table_score["header_score"] > 0:
            interpretation["summary"]["possible_order_header_tables"].append(
                {
                    "table_name": table_name,
                    "score": table_score["header_score"],
                    "matched_columns": table_score["header_matches"],
                }
            )

        if table_score["line_score"] > 0:
            interpretation["summary"]["possible_order_line_tables"].append(
                {
                    "table_name": table_name,
                    "score": table_score["line_score"],
                    "matched_columns": table_score["line_matches"],
                }
            )

        _suggest_column_mappings(
            table_name=table_name,
            column_names=column_names,
            mapping=interpretation["recommended_modula_mapping"],
        )

    interpretation["summary"]["possible_order_header_tables"].sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    interpretation["summary"]["possible_order_line_tables"].sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    output_path = (
        Path("generated_integrations")
        / "sql_connection_analysis"
        / "sql_schema_interpretation.json"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(interpretation, file, indent=4)

    interpretation["output_path"] = str(output_path)

    return interpretation


def _score_table(table_name: str, column_names: list[str]) -> dict:
    table_name_lower = table_name.lower()
    column_names_lower = [name.lower() for name in column_names]

    header_keywords = ["order", "orders", "salesorder", "customer", "ship"]
    line_keywords = ["line", "detail", "item", "sku", "part", "quantity", "qty"]

    header_score = 0
    line_score = 0
    header_matches = []
    line_matches = []

    for keyword in header_keywords:
        if keyword in table_name_lower:
            header_score += 3
            header_matches.append(f"table:{keyword}")

        for column_name in column_names_lower:
            if keyword in column_name:
                header_score += 1
                header_matches.append(column_name)

    for keyword in line_keywords:
        if keyword in table_name_lower:
            line_score += 3
            line_matches.append(f"table:{keyword}")

        for column_name in column_names_lower:
            if keyword in column_name:
                line_score += 1
                line_matches.append(column_name)

    return {
        "header_score": header_score,
        "line_score": line_score,
        "header_matches": sorted(set(header_matches)),
        "line_matches": sorted(set(line_matches)),
    }


def _suggest_column_mappings(
    table_name: str,
    column_names: list[str],
    mapping: dict,
) -> None:
    candidates = {
        "order_id": ["orderid", "order_id", "ordernumber", "order_number", "order"],
        "customer_name": ["customername", "customer_name", "customer", "client"],
        "ship_to_name": ["shiptoname", "ship_to_name", "shipname"],
        "ship_to_address": ["shiptoaddress", "ship_to_address", "address"],
        "item": ["itemnumber", "item_number", "item", "sku", "partnumber", "part_number"],
        "quantity": ["quantity", "qty", "orderqty", "order_qty"],
        "location": ["location", "locationcode", "location_code", "bin"],
    }

    for modula_field, possible_names in candidates.items():
        if mapping.get(modula_field) is not None:
            continue

        for column_name in column_names:
            normalized = column_name.lower().replace(" ", "").replace("-", "").replace("_", "")

            for possible_name in possible_names:
                possible_normalized = possible_name.lower().replace("_", "")

                if possible_normalized in normalized:
                    mapping[modula_field] = {
                        "table_name": table_name,
                        "column_name": column_name,
                    }
                    break

            if mapping.get(modula_field) is not None:
                break