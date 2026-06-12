"""
rest_api_connector.py

REST API connector for the Modula WMS Data Integration Agent.

This module supports two API-related functions:

1. Analyze REST API documentation using OpenAI
2. Execute live REST API GET requests and return JSON responses
"""

import json
from pathlib import Path
from typing import Any, Dict

import requests

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
    REST API connector and API documentation analyzer.
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

    def get_json(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        api_key: str | None = None,
        api_key_header: str = "Authorization",
        bearer_token: bool = True,
        timeout: int = 30,
        output_path: str | None = None,
    ) -> dict[str, Any]:
        request_headers = headers.copy() if headers else {}

        if api_key:
            if bearer_token:
                request_headers[api_key_header] = f"Bearer {api_key}"
            else:
                request_headers[api_key_header] = api_key

        try:
            response = requests.get(
                url,
                headers=request_headers,
                params=params,
                timeout=timeout,
            )

            response.raise_for_status()

            try:
                data = response.json()
            except ValueError:
                return {
                    "status": "error",
                    "source_type": "rest_api",
                    "message": "API response was not valid JSON.",
                    "url": url,
                    "status_code": response.status_code,
                    "raw_response": response.text[:2000],
                }

            result = {
                "status": "success",
                "source_type": "rest_api",
                "url": url,
                "status_code": response.status_code,
                "data": data,
            }

            if output_path:
                path = Path(output_path)
                path.parent.mkdir(parents=True, exist_ok=True)

                with open(path, "w", encoding="utf-8") as file:
                    json.dump(result, file, indent=4)

                result["output_path"] = str(path)

            return result

        except Exception as error:
            return {
                "status": "error",
                "source_type": "rest_api",
                "message": "REST API GET request failed.",
                "url": url,
                "error": str(error),
            }