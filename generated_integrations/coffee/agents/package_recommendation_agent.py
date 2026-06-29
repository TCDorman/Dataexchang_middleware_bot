"""
package_recommendation_agent.py

Converts an integration blueprint into a package generation recommendation.

This agent does not generate files. It decides which package generators
should be used and what information is still missing.
"""

from typing import Any


class PackageRecommendationAgent:
    """
    Recommends middleware package components based on an integration blueprint.
    """

    def recommend_packages(
        self,
        blueprint: dict[str, Any],
    ) -> dict[str, Any]:
        required_packages = blueprint.get("required_packages", [])
        data_flows = blueprint.get("data_flows", [])

        recommendations = []

        for package_type in required_packages:
            recommendations.append(
                self._build_recommendation(
                    package_type=package_type,
                    data_flows=data_flows,
                )
            )

        if not recommendations:
            recommendations.append(
                {
                    "package_type": "manual_review_required",
                    "reason": "No package type could be determined from the blueprint.",
                    "ready_to_generate": False,
                    "missing_inputs": [
                        "Integration method",
                        "Data flow details",
                        "Confirmed mappings",
                    ],
                }
            )

        return {
            "status": "success",
            "customer_name": blueprint.get("customer_name", "unknown_customer"),
            "integration_type": blueprint.get("integration_type", "unclear"),
            "recommended_packages": recommendations,
            "next_step": self._build_next_step(recommendations),
        }

    def _build_recommendation(
        self,
        package_type: str,
        data_flows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if package_type == "file_integration_package":
            return {
                "package_type": package_type,
                "reason": self._find_reason_for_method(
                    data_flows=data_flows,
                    method_tokens=[
                        "file",
                        "csv",
                        "json",
                        "xml",
                        "excel",
                        "xlsx",
                    ],
                    fallback="At least one flow appears to use file-based exchange.",
                ),
                "ready_to_generate": False,
                "missing_inputs": [
                    "Sample customer input file",
                    "Confirmed source-to-target field mapping",
                    "Expected Modula output format",
                    "Input/output folder locations",
                ],
            }

        if package_type == "rest_integration_package":
            return {
                "package_type": package_type,
                "reason": self._find_reason_for_method(
                    data_flows=data_flows,
                    method_tokens=[
                        "rest",
                        "api",
                        "http",
                        "web service",
                    ],
                    fallback="At least one flow appears to use REST/API exchange.",
                ),
                "ready_to_generate": False,
                "missing_inputs": [
                    "REST API base URL",
                    "Authentication method",
                    "Endpoint paths",
                    "Sample request/response payloads",
                    "Confirmed field mapping",
                ],
            }

        if package_type == "sql_integration_package":
            return {
                "package_type": package_type,
                "reason": self._find_reason_for_method(
                    data_flows=data_flows,
                    method_tokens=[
                        "sql",
                        "odbc",
                        "database",
                        "table",
                        "view",
                    ],
                    fallback="At least one flow appears to use SQL/ODBC database exchange.",
                ),
                "ready_to_generate": False,
                "missing_inputs": [
                    "SQL/ODBC connection details",
                    "Source and/or target table names",
                    "Primary key fields",
                    "Confirmed field mapping",
                    "Sample records or schema inspection output",
                ],
            }

        return {
            "package_type": package_type,
            "reason": "Package type requires manual review.",
            "ready_to_generate": False,
            "missing_inputs": [
                "Package type clarification",
                "Implementation details",
            ],
        }

    def _find_reason_for_method(
        self,
        data_flows: list[dict[str, Any]],
        method_tokens: list[str],
        fallback: str,
    ) -> str:
        matching_flows = []

        for flow in data_flows:
            method = str(flow.get("method", "")).lower()
            name = flow.get("name") or flow.get("data_object") or "Unnamed flow"
            direction = flow.get("direction", "unknown")
            source = flow.get("source_system", "")
            target = flow.get("target_system", "")

            if any(token in method for token in method_tokens):
                matching_flows.append(
                    f"{name} flow uses {method} exchange from {source} to {target} ({direction})."
                )

        if matching_flows:
            return " ".join(matching_flows)

        return fallback

    def _build_next_step(
        self,
        recommendations: list[dict[str, Any]],
    ) -> str:
        if all(item.get("ready_to_generate") for item in recommendations):
            return "All recommended packages appear ready to generate."

        return (
            "Collect the missing inputs for each recommended package, then run package generation."
        )