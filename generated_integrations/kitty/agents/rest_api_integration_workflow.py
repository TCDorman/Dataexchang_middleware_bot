"""
rest_api_integration_workflow.py

High-level orchestration for generating a complete REST integration package.
"""

from pathlib import Path

from src.connectors.rest_api_connector import RestApiConnector
from src.generators.rest_integration_package_generator import (
    RestIntegrationPackageGenerator,
)


class RestApiIntegrationWorkflow:
    """
    Coordinates REST analysis and package generation.
    """

    def __init__(self):
        self.connector = RestApiConnector()
        self.package_generator = RestIntegrationPackageGenerator()

    def generate_from_documentation(
        self,
        customer_name: str,
        documentation_text: str,
        pull_url: str,
        push_url: str,
        push_source_path: str,
        push_field_mapping: dict[str, str],
        output_base_folder: str = "generated_integrations",
    ) -> dict:
        output_folder = self._get_customer_output_folder(
            customer_name=customer_name,
            output_base_folder=output_base_folder,
        )

        analysis = self.connector.analyze_api_documentation(
            documentation_text=documentation_text,
        )

        package = self.package_generator.generate_package(
            customer_name=customer_name,
            output_folder=str(output_folder),
            pull_url=pull_url,
            push_url=push_url,
            push_source_path=push_source_path,
            push_field_mapping=push_field_mapping,
        )

        return {
            "status": "success",
            "source_type": "rest_api",
            "customer_name": customer_name,
            "analysis": analysis,
            "package": package,
        }

    def generate_manual_package(
        self,
        customer_name: str,
        pull_url: str,
        push_url: str,
        push_source_path: str,
        push_field_mapping: dict[str, str],
        output_base_folder: str = "generated_integrations",
    ) -> dict:
        output_folder = self._get_customer_output_folder(
            customer_name=customer_name,
            output_base_folder=output_base_folder,
        )

        package = self.package_generator.generate_package(
            customer_name=customer_name,
            output_folder=str(output_folder),
            pull_url=pull_url,
            push_url=push_url,
            push_source_path=push_source_path,
            push_field_mapping=push_field_mapping,
        )

        return {
            "status": "success",
            "source_type": "rest_api",
            "customer_name": customer_name,
            "package": package,
        }

    def _get_customer_output_folder(
        self,
        customer_name: str,
        output_base_folder: str,
    ) -> Path:
        safe_customer_name = customer_name.strip().lower().replace(" ", "_")
        return Path(output_base_folder) / safe_customer_name