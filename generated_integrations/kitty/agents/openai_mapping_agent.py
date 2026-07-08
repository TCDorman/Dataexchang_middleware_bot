"""
==================================================
OpenAI Mapping Agent
==================================================

Purpose:
    Uses OpenAI to infer field mappings between
    customer data and the Modula WMS schema.

Responsibilities:
    - Analyze unknown customer fields
    - Suggest Modula-compatible mappings
    - Return mappings as structured JSON

Example:

Input:
{
    "OrderNumber": "1001",
    "Customer": "Ford",
    "PartNumber": "ABC123",
    "Qty": 5
}

Output:
{
    "order_id": "OrderNumber",
    "customer_name": "Customer",
    "item": "PartNumber",
    "quantity": "Qty"
}
"""

# ==================================================
# Imports
# ==================================================

import json

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

# ==================================================
# OpenAI Mapping Agent
# ==================================================

class OpenAIMappingAgent:
    """
    AI-powered field mapping generator.
    """

    def __init__(self):
        """
        Initialize OpenAI client.
        """

        self.client = OpenAIClient()

    def infer_mapping(
        self,
        sample_record: dict,
    ) -> dict:
        """
        Infer Modula field mappings from
        a customer sample record.

        Args:
            sample_record:
                Sample customer record.

        Returns:
            Dictionary containing mapping suggestions.
        """

        prompt = f"""
You are a warehouse integration expert.

A customer has provided the following order data:

{json.dumps(sample_record, indent=4)}

Determine which fields correspond to the following
Modula WMS fields:

- order_id
- customer_name
- item
- quantity

Return ONLY valid JSON.

Example:

{{
    "order_id": "OrderNumber",
    "customer_name": "Customer",
    "item": "PartNumber",
    "quantity": "Qty"
}}
"""

        response = self.client.ask(prompt)

        cleaned_response = clean_json_response(response)

        try:
            return json.loads(cleaned_response)

        except Exception:
            return {
                "error": "Failed to parse AI response.",
                "raw_response": response,
            }


# ==================================================
# Convenience Function
# ==================================================

def infer_mapping_with_openai(
    sample_record: dict,
) -> dict:
    """
    Simple helper function for direct usage.

    Args:
        sample_record:
            Sample customer record.

    Returns:
        AI-generated mapping.
    """

    agent = OpenAIMappingAgent()

    return agent.infer_mapping(sample_record)