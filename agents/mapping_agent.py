import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def suggest_wms_mappings(fields):
    prompt = f"""
You are a Modula WMS integration assistant.

Given these customer ERP field names:

{fields}

Suggest the most likely Modula WMS mappings.

Return ONLY valid JSON in this format:

{{
    "mappings": [
        {{
            "source_field": "sku",
            "suggested_wms_field": "ART_ARTICOLO",
            "confidence": 0.98
        }}
    ]
}}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a WMS integration expert."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    sample_fields = [
        "sku",
        "description",
        "quantity",
        "order_number",
        "item_code"
    ]

    result = suggest_wms_mappings(sample_fields)

    print("\nLLM MAPPING SUGGESTIONS")
    print(result)