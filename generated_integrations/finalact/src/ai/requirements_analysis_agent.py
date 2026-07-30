"""
requirements_analysis_agent.py

Uses OpenAI to analyze customer ERP/WMS integration requirements
and produce implementation-ready middleware planning outputs.
"""

import json
from typing import Any

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


class RequirementsAnalysisAgent:
    """
    Analyzes customer integration requirements and produces
    structured implementation guidance.
    """

    def __init__(self):
        self.openai_client = OpenAIClient()

    def analyze_requirements(
        self,
        requirements_text: str,
    ) -> dict[str, Any]:
        prompt = f"""
You are a middleware implementation assistant for Modula USA.

Your job is to analyze customer ERP/WMS integration requirements and produce
implementation-ready technical planning output.

The system supports these integration methods:
1. File-based exchange: CSV, JSON, XML, Excel
2. REST API exchange
3. SQL / ODBC database exchange

Focus on Modula WMS integration workflows involving:
- orders / ordini
- item master / articoli
- inventory transactions
- serial numbers
- shipment or fulfillment data
- customer ERP/WMS platforms such as SAP, Oracle, NetSuite, Microsoft Dynamics, Epicor, Infor, Sage, or custom systems

Return ONLY valid JSON.

JSON format:

{{
    "status": "success",
    "integration_summary": "",
    "source_systems": [],
    "target_systems": [],
    "data_flows": [
        {{
            "flow_name": "",
            "direction": "",
            "source_system": "",
            "target_system": "",
            "data_object": "",
            "recommended_exchange_method": "",
            "frequency": "",
            "notes": ""
        }}
    ],
    "field_mapping_candidates": [
        {{
            "data_object": "",
            "canonical_modula_field": "",
            "possible_customer_fields": [],
            "transformation_notes": ""
        }}
    ],
    "transformation_rules": [],
    "error_handling_recommendations": [],
    "serialization_or_lot_tracking_notes": [],
    "implementation_checklist": [],
    "customer_clarification_questions": [],
    "risk_flags": []
}}

Customer Requirements:

{requirements_text}
"""

        response = self.openai_client.ask(prompt)
        cleaned = clean_json_response(response)

        try:
            return json.loads(cleaned)

        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": "OpenAI returned invalid JSON.",
                "raw_response": response,
            }