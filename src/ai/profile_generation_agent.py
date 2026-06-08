"""
profile_generation_agent.py

Uses OpenAI to generate customer profiles from unknown CSV headers.

This AI component creates:
- header signatures
- field mappings
- confidence scores
- mapping notes
"""

import json
from typing import Dict, List

from src.ai.openai_client import OpenAIClient

# ==================================================
# Response Cleaning
# ==================================================

def clean_json_response(response_text: str) -> str:
    """
    Remove markdown code fences from an AI response.

    Args:
        response_text:
            Raw response returned by OpenAI.

    Returns:
        Clean JSON string.
    """

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
        """
        Initialize AI client.
        """

        self.openai_client = OpenAIClient()

    def generate_profile(
        self,
        headers: List[str],
    ) -> Dict:
        """
        Generate a customer profile from CSV headers.

        Args:
            headers: List of CSV column names.

        Returns:
            Generated profile dictionary.
        """

        prompt = f"""
You are a warehouse integration expert.

Map the provided CSV headers into this internal schema:

- order_id
- customer_name
- item
- quantity

CSV headers:
{headers}

Return ONLY valid JSON.
Do not include markdown.
Do not include explanation.
Do not wrap the JSON in code fences.

The JSON must follow this exact structure:

{{
    "customer_name": "Unknown Customer",
    "header_signature": {headers},
    "field_mapping": {{
        "SOURCE_HEADER": "INTERNAL_FIELD"
    }},
    "mapping_confidence": {{
        "SOURCE_HEADER": 95
    }},
    "mapping_notes": {{
        "SOURCE_HEADER": "Short reason for this mapping."
    }}
}}

Rules:
- Confidence must be an integer from 0 to 100.
- Only map headers that clearly match the internal schema.
- Do not invent source headers that are not in the CSV headers.
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