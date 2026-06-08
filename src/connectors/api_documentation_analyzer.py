"""
==================================================
API Documentation Analyzer
==================================================

Purpose:
    Analyzes customer API documentation or sample API
    responses and produces a structured integration plan.

Responsibilities:
    - Identify likely base URL
    - Identify likely order endpoint
    - Identify authentication type
    - Extract response schema clues
    - Suggest Modula WMS field mappings
"""

# ==================================================
# Imports
# ==================================================

import json
from typing import Dict

from src.ai.openai_client import OpenAIClient


# ==================================================
# Response Cleaning
# ==================================================

def clean_json_response(response_text: str) -> str:
    """
    Remove markdown formatting from an AI JSON response.
    """

    cleaned = response_text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned.replace("```json", "", 1)

    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```", "", 1)

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return cleaned.strip()


# ==================================================
# API Documentation Analyzer
# ==================================================

class ApiDocumentationAnalyzer:
    """
    Uses AI to analyze customer API documentation.
    """

    def __init__(self):
        """
        Initialize OpenAI client.
        """

        self.openai_client = OpenAIClient()

    def analyze_documentation(
        self,
        documentation_text: str,
    ) -> Dict:
        """
        Analyze customer API documentation text.

        Args:
            documentation_text:
                Raw API documentation or sample response text.

        Returns:
            Structured API integration plan.
        """

        prompt = f"""
You are an API integration architect for a warehouse
management system integration project.

Analyze the following customer API documentation or sample
API response and create a structured integration plan.

Customer API Documentation:
{documentation_text}

Return ONLY valid JSON.
Do not include markdown.
Do not include explanations outside JSON.

The JSON must follow this exact structure:

{{
    "customer_name": "Unknown API Customer",
    "base_url": "",
    "orders_endpoint": "",
    "auth_type": "api_key | bearer_token | basic_auth | none | unknown",
    "api_key_header": "",
    "api_key_env_var": "",
    "http_method": "GET",
    "response_root": "",
    "response_schema": {{}},
    "suggested_mapping": {{
        "order_number": "",
        "description": "",
        "operation_type": "",
        "lines": {{
            "item_code": "",
            "quantity": ""
        }}
    }},
    "confidence": {{
        "base_url": 0,
        "orders_endpoint": 0,
        "auth_type": 0,
        "suggested_mapping": 0
    }},
    "notes": []
}}

Rules:
- If a value is unknown, use an empty string or "unknown".
- Do not invent fake URLs.
- Do not invent authentication secrets.
- Use confidence values from 0 to 100.
- Map fields to Modula WMS-style structures.
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