"""
profile_generation_agent.py

Uses OpenAI to generate customer profiles from unknown CSV headers.
"""

import json
from typing import Dict, List

from src.ai.openai_client import OpenAIClient


def clean_json_response(response_text: str) -> str:
    cleaned = response_text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned.replace("```json", "", 1)

    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```", "", 1)

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return cleaned.strip()


class ProfileGenerationAgent:
    """
    Generates customer profiles using OpenAI.
    """

    def __init__(self):
        self.openai_client = OpenAIClient()

    def generate_profile(
        self,
        customer_name: str,
        source_type: str,
        headers: List[str],
        field_mapping: Dict[str, str],
    ) -> Dict:
        prompt = f"""
You are a warehouse integration expert.

Create a customer integration profile for Modula WMS.

Customer name:
{customer_name}

Source type:
{source_type}

CSV headers:
{headers}

Field mapping:
{field_mapping}

Return ONLY valid JSON.
Do not include markdown.
Do not include explanation.
Do not wrap the JSON in code fences.

The JSON must follow this exact structure:

{{
    "customer_name": "{customer_name}",
    "source_type": "{source_type}",
    "target_system": "Modula WMS",
    "target_format": "XML",
    "header_signature": {headers},
    "field_mapping": {field_mapping},
    "validation_rules": {{
        "order_id": "required",
        "customer_name": "optional",
        "item": "required",
        "quantity": "required_numeric"
    }},
    "mapping_confidence": {{
        "order_id": 95,
        "customer_name": 95,
        "item": 95,
        "quantity": 95
    }},
    "mapping_notes": {{
        "order_id": "Short reason.",
        "customer_name": "Short reason.",
        "item": "Short reason.",
        "quantity": "Short reason."
    }}
}}

Rules:
- field_mapping must map internal Modula fields to customer source headers.
- Do not invent source headers that are not in the CSV headers.
- Confidence must be an integer from 0 to 100.
- Use higher confidence for obvious matches.
- Use lower confidence for ambiguous matches.
"""

        response = self.openai_client.ask(prompt)
        cleaned_response = clean_json_response(response)

        try:
            return json.loads(cleaned_response)

        except json.JSONDecodeError as error:
            raise ValueError(
                "OpenAI did not return valid JSON.\n"
                f"Raw response: {response}\n"
                f"Cleaned response: {cleaned_response}"
            ) from error