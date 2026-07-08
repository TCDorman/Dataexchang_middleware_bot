"""
auto_integration_workflow.py

High-level AI workflow that analyzes customer requirements and determines
what integration package or implementation artifacts should be generated.

This is intended to reduce manual user input. The user provides requirements,
sample data, API notes, or SQL notes, and the agent decides the likely
integration path.
"""

from typing import Any

from agents.integration_blueprint_generator import IntegrationBlueprintGenerator
from agents.package_generation_planner import PackageGenerationPlanner
from agents.package_recommendation_agent import PackageRecommendationAgent
from src.ai.requirements_analysis_agent import RequirementsAnalysisAgent


class AutoIntegrationWorkflow:
    """
    Coordinates AI-driven middleware implementation planning.
    """

    def __init__(self):
        self.requirements_agent = RequirementsAnalysisAgent()
        self.blueprint_generator = IntegrationBlueprintGenerator()
        self.package_recommendation_agent = PackageRecommendationAgent()
        self.package_generation_planner = PackageGenerationPlanner()

    def run_from_requirements(
        self,
        requirements_text: str,
        output_base_folder: str = "generated_integrations",
    ) -> dict[str, Any]:
        analysis = self.requirements_agent.analyze_requirements(
            requirements_text=requirements_text,
        )

        if analysis.get("status") == "error":
            return analysis

        detected_type = self._detect_integration_type(analysis)

        missing_information = self._find_missing_information(
            analysis=analysis,
            detected_type=detected_type,
        )

        package_generation_ready = len(missing_information) == 0

        result = {
            "status": "success",
            "workflow": "auto_integration",
            "detected_integration_type": detected_type,
            "package_generation_ready": package_generation_ready,
            "analysis": analysis,
            "missing_information": missing_information,
            "recommended_next_action": self._get_recommended_next_action(
                detected_type=detected_type,
                package_generation_ready=package_generation_ready,
                missing_information=missing_information,
            ),
            "output_base_folder": output_base_folder,
        }

        result["blueprint"] = self.blueprint_generator.generate_blueprint(
            analysis_result=result,
            detected_integration_type=detected_type,
        )

        result["package_recommendation"] = (
            self.package_recommendation_agent.recommend_packages(
                blueprint=result["blueprint"],
            )
        )

        result["generation_plan"] = self.package_generation_planner.build_plan(
            package_recommendation=result["package_recommendation"],
        )

        return result

    def _detect_integration_type(
        self,
        analysis: dict[str, Any],
    ) -> str:
        data_flows = analysis.get("data_flows", [])

        methods = []

        for flow in data_flows:
            method = str(
                flow.get("recommended_exchange_method", "")
            ).strip().lower()

            if method:
                methods.append(method)

        joined_methods = " ".join(methods)

        has_file = any(
            token in joined_methods
            for token in [
                "file",
                "csv",
                "json",
                "xml",
                "excel",
                "xlsx",
            ]
        )

        has_rest = any(
            token in joined_methods
            for token in [
                "rest",
                "api",
                "http",
                "web service",
            ]
        )

        has_sql = any(
            token in joined_methods
            for token in [
                "sql",
                "odbc",
                "database",
                "table",
                "view",
            ]
        )

        detected = []

        if has_file:
            detected.append("file")

        if has_rest:
            detected.append("rest_api")

        if has_sql:
            detected.append("sql")

        if len(detected) > 1:
            return "hybrid"

        if detected:
            return detected[0]

        return "unclear"

    def _find_missing_information(
        self,
        analysis: dict[str, Any],
        detected_type: str,
    ) -> list[str]:
        missing = []

        if detected_type == "unclear":
            missing.append(
                "Integration method is unclear. Need to know whether the customer uses file exchange, REST API, SQL/ODBC, or a hybrid flow."
            )

        if detected_type in ["file", "hybrid"]:
            missing.extend(
                [
                    "Sample input/output files are needed.",
                    "File format details are needed: CSV, JSON, XML, Excel, delimiter, headers, encoding.",
                    "Folder locations or transfer method are needed.",
                ]
            )

        if detected_type in ["rest_api", "hybrid"]:
            missing.extend(
                [
                    "REST API base URL is needed.",
                    "Authentication method is needed.",
                    "Order/item/inventory endpoint details are needed.",
                    "Sample API request/response payloads are needed.",
                ]
            )

        if detected_type in ["sql", "hybrid"]:
            missing.extend(
                [
                    "SQL/ODBC connection details are needed.",
                    "Source or target table names are needed.",
                    "Required SQL fields and keys are needed.",
                ]
            )

        if not analysis.get("field_mapping_candidates"):
            missing.append(
                "Field mapping candidates are missing or incomplete."
            )

        if not analysis.get("data_flows"):
            missing.append(
                "Data flows are missing or incomplete."
            )

        return missing

    def _get_recommended_next_action(
        self,
        detected_type: str,
        package_generation_ready: bool,
        missing_information: list[str],
    ) -> str:
        if package_generation_ready:
            return (
                "Sufficient information appears available. "
                "Review the AI analysis, confirm mappings, "
                "and generate the integration package."
            )

        if detected_type == "hybrid":
            return (
                "Hybrid integration detected. Collect the missing "
                "file/API/SQL details, then generate separate package "
                "components for each flow."
            )

        if detected_type == "file":
            return (
                "File-based integration detected. Collect sample customer "
                "files and confirm field mappings before package generation."
            )

        if detected_type == "rest_api":
            return (
                "REST API integration detected. Collect API base URL, "
                "authentication details, endpoint documentation, and "
                "sample payloads before package generation."
            )

        if detected_type == "sql":
            return (
                "SQL/ODBC integration detected. Collect connection details, "
                "table names, key fields, and sample records before package generation."
            )

        return (
            "More discovery is required before package generation. "
            "Ask the customer the listed clarification questions."
        )