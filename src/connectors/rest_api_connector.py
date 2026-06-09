"""
rest_api_connector.py

Uses OpenAI to analyze REST API documentation and generate
an integration profile.
"""

import json
from typing import Dict

from src.ai.openai_client import OpenAIClient


def clean_json_response(response_text: str) -> str:
    """
    Remove markdown code fences from OpenAI responses.
    """

    cleaned = response_text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned.replace("```json", "", 1)

    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```", "", 1)

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return cleaned.strip()


class RestApiConnector:
    """
    AI-powered REST API documentation analyzer.
    """

    def __init__(self):
        self.openai_client = OpenAIClient()

    def analyze_api_documentation(
        self,
        documentation_text: str,
    ) -> Dict:

        prompt = f"""
You are a warehouse integration expert.

Analyze the following API documentation.

Determine:

1. Which endpoint most likely contains order data
2. Which fields map to:
   - order_id
   - customer_name
   - item
   - quantity

Return ONLY valid JSON.

JSON format:

{{
    "source_type": "rest_api",
    "order_endpoint": "",
    "field_mapping": {{
        "order_id": "",
        "customer_name": "",
        "item": "",
        "quantity": ""
    }},
    "confidence_score": 0,
    "notes": []
}}

API Documentation:

{documentation_text[:12000]}
"""

        response = self.openai_client.ask(prompt)

        cleaned = clean_json_response(response)

        try:
            result = json.loads(cleaned)

            result["status"] = "success"

            return result

        except json.JSONDecodeError:

            return {
                "status": "error",
                "source_type": "rest_api",
                "message": "OpenAI returned invalid JSON.",
                "raw_response": response,
            }