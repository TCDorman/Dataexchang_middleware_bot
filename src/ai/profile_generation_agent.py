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

        try:
            return json.loads(response)

        except json.JSONDecodeError as error:
            raise ValueError(
                f"OpenAI did not return valid JSON. Raw response: {response}"
            ) from error