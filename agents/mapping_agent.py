import sys
from pathlib import Path
import os
import json

sys.path.append(str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
from openai import OpenAI

from models.mapping_models import MappingResponse

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


KNOWN_WMS_FIELDS = [
    {
        "wms_field": "ORD_ORDINE",
        "internal_field": "order_number",
        "description": "Order number"
    },
    {
        "wms_field": "ORD_DES",
        "internal_field": "description",
        "description": "Order description"
    },
    {
        "wms_field": "ORD_TIPOOP",
        "internal_field": "operation_type",
        "description": "Operation type"
    },
    {
        "wms_field": "RIG_ARTICOLO",
        "internal_field": "item_code",
        "description": "Item/SKU code"
    },
    {
        "wms_field": "RIG_QTAR",
        "internal_field": "quantity",
        "description": "Requested quantity"
    }
]


def suggest_wms_mappings(source_fields: list[str]):

    prompt = f"""
You are an ERP to WMS integration expert.

Customer ERP fields:
{source_fields}

Known Modula WMS fields:
{json.dumps(KNOWN_WMS_FIELDS, indent=4)}

Determine the best mapping between the customer fields and WMS fields.

Return ONLY valid JSON in this format:

{{
    "mappings": [
        {{
            "source_field": "customer field",
            "suggested_wms_field": "WMS field",
            "internal_field": "internal normalized field",
            "confidence": 0.95,
            "reason": "brief explanation"
        }}
    ]
}}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an expert ERP integration architect."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    content = (
        content
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    parsed = json.loads(content)

    return MappingResponse(**parsed)


if __name__ == "__main__":

    sample_fields = [
        "client_order_ref",
        "company_name",
        "process_type",
        "material_code",
        "requested_quantity",
    ]

    result = suggest_wms_mappings(sample_fields)

    print("\nAI FIELD MAPPINGS\n")

    for mapping in result.mappings:
        print(mapping)