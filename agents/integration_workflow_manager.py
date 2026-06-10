"""
integration_workflow_manager.py

Central workflow router for the Modula WMS Data Integration Agent.
"""

from pathlib import Path

from agents.api_documentation_analyzer import analyze_api_documentation_file
from agents.demo_workflow_agent import run_demo_workflow
from agents.full_ai_onboarding_runner import run_full_ai_onboarding
from agents.live_sql_to_modula_xml_agent import generate_modula_xml_from_live_sql
from agents.sql_connection_analyzer import analyze_sql_connection_string
from src.connectors.source_detector import SourceDetector
from agents.openai_profile_review_agent import review_customer_profile


class IntegrationWorkflowManager:
    API_DOC_EXTENSIONS = {".txt", ".md", ".yaml", ".yml"}

    def run_file_workflow(
        self,
        file_path: str,
        customer_name: str,
    ) -> dict:
        source_type = self.detect_source_kind(file_path)

        if source_type == "api_documentation":
            return analyze_api_documentation_file(file_path)

        if source_type in ["csv", "json", "xml"]:
            return run_full_ai_onboarding(
                customer_name=customer_name,
                source_type=source_type,
                file_path=file_path,
            )

        return {
            "status": "error",
            "message": f"Unsupported source type: {source_type}",
            "file_path": file_path,
        }

    def run_sql_analysis_workflow(
        self,
        connection_string: str,
    ) -> dict:
        return analyze_sql_connection_string(connection_string)

    def run_live_sql_to_xml_workflow(
        self,
        connection_string: str,
        profile_path: str,
    ) -> dict:
        return generate_modula_xml_from_live_sql(
            connection_string=connection_string,
            profile_path=profile_path,
        )

    def run_demo_workflow(self) -> dict:
        return run_demo_workflow()

    def detect_source_kind(self, file_path: str) -> str:
        suffix = Path(file_path).suffix.lower()

        if suffix in self.API_DOC_EXTENSIONS:
            return "api_documentation"

        if suffix == ".json" and self._is_openapi_json(file_path):
            return "api_documentation"

        return SourceDetector.detect_source_type(file_path)
    def run_profile_review_workflow(self, profile_path: str) -> dict:
        return review_customer_profile(profile_path)
    def _is_openapi_json(self, file_path: str) -> bool:
        import json

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            return isinstance(data, dict) and (
                "openapi" in data
                or "swagger" in data
                or "paths" in data
            )

        except Exception:
            return False