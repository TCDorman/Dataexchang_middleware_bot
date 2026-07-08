"""
sql_integration_workflow.py

High-level workflow for generating a complete SQL integration package.
"""

from pathlib import Path

from src.generators.sql_integration_package_generator import (
    SQLIntegrationPackageGenerator,
)


class SQLIntegrationWorkflow:
    """
    Coordinates SQL package generation.
    """

    def __init__(self):
        self.package_generator = SQLIntegrationPackageGenerator()

    def generate_manual_package(
        self,
        customer_name: str,
        connection_string: str,
        pull_query: str,
        push_source_path: str,
        push_target_table: str,
        push_field_mapping: dict[str, str],
        database_type: str = "sqlite",
        output_base_folder: str = "generated_integrations",
    ) -> dict:
        output_folder = self._get_customer_output_folder(
            customer_name=customer_name,
            output_base_folder=output_base_folder,
        )

        package = self.package_generator.generate_package(
            customer_name=customer_name,
            output_folder=str(output_folder),
            connection_string=connection_string,
            database_type=database_type,
            pull_query=pull_query,
            push_source_path=push_source_path,
            push_target_table=push_target_table,
            push_field_mapping=push_field_mapping,
        )

        return {
            "status": "success",
            "source_type": "sql",
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