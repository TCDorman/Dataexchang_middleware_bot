"""
field_mapping_agent.py

Uses OpenAI to suggest mappings between customer file fields
and Modula WMS target fields.
"""

import json

from src.ai.openai_client import OpenAIClient


class FieldMappingAgent:
    """
    AI-powered field mapping assistant.
    """

    def __init__(self):
        self.openai_client = OpenAIClient()

    def clean_json_response(self, response: str) -> str:
        cleaned = response.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned.replace("```json", "", 1).strip()

        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```", "", 1).strip()

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

        return cleaned

    def suggest_mapping(
        self,
        source_fields: list[str],
        target_fields: list[str],
    ) -> dict:
        prompt = f"""
You are helping map a customer's source file fields to Modula WMS target fields.

Source fields:
{source_fields}

Target fields:
{target_fields}

Return only raw valid JSON.
Do not include markdown.
Do not include code fences.
The JSON should map each target field to the best matching source field.

Example:
{{
    "order_id": "Order Number",
    "customer_name": "Customer",
    "item": "SKU",
    "quantity": "Qty"
}}
"""

        response = self.openai_client.ask(prompt)
        cleaned_response = self.clean_json_response(response)

        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": "OpenAI returned invalid JSON.",
                "raw_response": response,
                "cleaned_response": cleaned_response,
            }


if __name__ == "__main__":
    agent = FieldMappingAgent()

    result = agent.suggest_mapping(
        source_fields=[
            "Order Number",
            "Customer",
            "SKU",
            "Qty",
        ],
        target_fields=[
            "order_id",
            "customer_name",
            "item",
            "quantity",
        ],
    )

    print(json.dumps(result, indent=4))