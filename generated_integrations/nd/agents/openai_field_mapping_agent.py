"""
openai_field_mapping_agent.py

OpenAI-powered field mapping agent.

Purpose:
1. Accept customer/source column names
2. Ask OpenAI to map them to Modula WMS fields
3. Return confidence scores and notes
4. Fall back safely to rule-based mapping if OpenAI is unavailable
"""

import json
import os
from typing import Any
from dotenv import load_dotenv
load_dotenv()

MODULA_FIELDS = [
    "order_id",
    "customer_name",
    "ship_to_name",
    "ship_to_address",
    "item",
    "quantity",
    "location",
]


def infer_field_mapping_with_openai(
    source_columns: list[str],
    source_type: str = "csv",
) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return _fallback_mapping(
            source_columns=source_columns,
            source_type=source_type,
            reason="OPENAI_API_KEY is not set.",
        )

    try:
        from openai import OpenAI
    except ImportError:
        return _fallback_mapping(
            source_columns=source_columns,
            source_type=source_type,
            reason="openai package is not installed. Run: pip install openai",
        )

    client = OpenAI(api_key=api_key)

    prompt = {
        "task": "Map customer source columns to Modula WMS fields.",
        "source_type": source_type,
        "source_columns": source_columns,
        "target_fields": MODULA_FIELDS,
        "requirements": {
            "return_json_only": True,
            "include_confidence_0_to_100": True,
            "include_mapping_notes": True,
            "use_null_when_no_good_match": True,
        },
        "expected_json_shape": {
            "status": "success",
            "source_type": source_type,
            "field_mapping": {
                "order_id": "source column or null",
                "customer_name": "source column or null",
                "ship_to_name": "source column or null",
                "ship_to_address": "source column or null",
                "item": "source column or null",
                "quantity": "source column or null",
                "location": "source column or null",
            },
            "mapping_confidence": {
                "order_id": 0,
                "customer_name": 0,
                "ship_to_name": 0,
                "ship_to_address": 0,
                "item": 0,
                "quantity": 0,
                "location": 0,
            },
            "mapping_notes": {
                "order_id": "reason",
                "customer_name": "reason",
                "ship_to_name": "reason",
                "ship_to_address": "reason",
                "item": "reason",
                "quantity": "reason",
                "location": "reason",
            },
        },
    }

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert WMS/ERP data integration analyst. "
                        "Return only valid JSON. Do not include markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(prompt, indent=2),
                },
            ],
            temperature=0,
        )

        content = response.choices[0].message.content
        parsed = json.loads(content)

        parsed["mapping_method"] = "openai"
        return parsed

    except Exception as error:
        return _fallback_mapping(
            source_columns=source_columns,
            source_type=source_type,
            reason=f"OpenAI mapping failed: {error}",
        )


def _fallback_mapping(
    source_columns: list[str],
    source_type: str,
    reason: str,
) -> dict[str, Any]:
    field_mapping = {}
    mapping_confidence = {}
    mapping_notes = {}

    for modula_field in MODULA_FIELDS:
        best_column = _find_best_column_match(modula_field, source_columns)

        if best_column:
            field_mapping[modula_field] = best_column
            mapping_confidence[modula_field] = 85
            mapping_notes[modula_field] = (
                f"Rule-based fallback matched {best_column} to {modula_field}."
            )
        else:
            field_mapping[modula_field] = None
            mapping_confidence[modula_field] = 0
            mapping_notes[modula_field] = "No confident rule-based match found."

    return {
        "status": "success",
        "source_type": source_type,
        "mapping_method": "fallback_rule_based",
        "fallback_reason": reason,
        "field_mapping": field_mapping,
        "mapping_confidence": mapping_confidence,
        "mapping_notes": mapping_notes,
    }


def _find_best_column_match(
    modula_field: str,
    source_columns: list[str],
) -> str | None:
    candidates = {
        "order_id": ["orderid", "order_id", "ordernumber", "order_number", "order"],
        "customer_name": ["customername", "customer_name", "customer", "client"],
        "ship_to_name": ["shiptoname", "ship_to_name", "shipname"],
        "ship_to_address": ["shiptoaddress", "ship_to_address", "address"],
        "item": ["itemnumber", "item_number", "item", "sku", "partnumber", "part_number"],
        "quantity": ["quantity", "qty", "orderqty", "order_qty"],
        "location": ["location", "locationcode", "location_code", "bin"],
    }

    possible_names = candidates.get(modula_field, [])

    for column in source_columns:
        normalized_column = _normalize(column)

        for possible_name in possible_names:
            if _normalize(possible_name) in normalized_column:
                return column

    return None


def _normalize(value: str) -> str:
    return (
        value.lower()
        .replace(" ", "")
        .replace("_", "")
        .replace("-", "")
        .replace(".", "")
    )