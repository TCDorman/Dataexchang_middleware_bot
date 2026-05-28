import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def suggest_wms_mappings(source_fields: list[str]):
    prompt = f"""
You are a Modula WMS integration assistant.

Given these customer ERP field names:

{source_fields}

Map them to the most likely Modula WMS fields.

Available WMS fields:
- ART_ARTICOLO: item code / SKU
- ART_DES: item description
- ORD_ORDINE: order number
- ORD_DES: order description
- ORD_TIPOOP: operation type
- RIG_ORDINE: order number reference
- RIG_ARTICOLO: item code on order line
- RIG_QTAR: requested quantity

Return ONLY valid JSON in this exact format:

{{
    "mappings": [
        {{
            "source_field": "source field name",
            "suggested_wms_field": "WMS field name",
            "internal_field": "normalized internal field",
            "confidence": 0.95,
            "reason": "short reason"
        }}
    ]
}}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an expert in ERP to WMS field mapping."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    # Remove optional markdown code fences if the model returns them
    content = content.replace("```json", "").replace("```", "").strip()

    return json.loads(content)


if __name__ == "__main__":
    sample_fields = [
        "client_order_ref",
        "company_name",
        "process_type",
        "material_code",
        "requested_quantity"
    ]

    result = suggest_wms_mappings(sample_fields)

    print("\nLLM MAPPING SUGGESTIONS")
    print(json.dumps(result, indent=4))