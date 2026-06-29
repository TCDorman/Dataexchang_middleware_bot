"""
==================================================
API Integration Generator
==================================================

Purpose:
    Generates customer API integration assets from
    analyzer output.

Responsibilities:
    - Generate REST API config
    - Generate mapping JSON
    - Create integration folder
    - Generate runnable starter files
    - Return generation results
"""

# ==================================================
# Imports
# ==================================================

import json
from pathlib import Path
from typing import Dict

from src.connectors.api_runner_generator import (
    ApiRunnerGenerator,
)


# ==================================================
# API Integration Generator
# ==================================================

class ApiIntegrationGenerator:
    """
    Generates customer API integration packages.
    """

    def generate(
        self,
        analysis_result: Dict,
    ) -> Dict:
        """
        Generate integration assets from analyzer output.
        """

        customer_name = self._get_safe_customer_name(
            analysis_result
        )

        integration_folder = (
            Path("generated_integrations")
            / customer_name
        )

        integration_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        config_path = self._generate_api_config(
            customer_name,
            analysis_result,
        )

        mapping_path = self._generate_mapping_file(
            integration_folder,
            analysis_result,
        )

        runner_generator = ApiRunnerGenerator()

        runner_files = runner_generator.generate_runner_files(
            folder=integration_folder,
            customer_name=customer_name,
            analysis_result=analysis_result,
            api_config_path=config_path,
        )

        self._generate_readme(
            integration_folder,
            analysis_result,
            mapping_path,
        )

        return {
            "status": "success",
            "customer_name": customer_name,
            "integration_folder": str(integration_folder),
            "config_path": config_path,
            "mapping_path": mapping_path,
            "runner_files": runner_files,
        }

    def _get_safe_customer_name(
        self,
        analysis_result: Dict,
    ) -> str:
        """
        Convert customer name into safe folder/file name.
        """

        return (
            analysis_result.get(
                "customer_name",
                "unknown_customer",
            )
            .strip()
            .lower()
            .replace(" ", "_")
        )

    def _generate_api_config(
        self,
        customer_name: str,
        analysis_result: Dict,
    ) -> str:
        """
        Create REST API config file.
        """

        config_folder = Path("configs/rest")

        config_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        config_path = (
            config_folder
            / f"{customer_name}_api.json"
        )

        config = {
            "customer_name": customer_name,
            "base_url": analysis_result.get(
                "base_url",
                "",
            ),
            "orders_endpoint": analysis_result.get(
                "orders_endpoint",
                "",
            ),
            "auth_type": analysis_result.get(
                "auth_type",
                "unknown",
            ),
            "api_key_header": analysis_result.get(
                "api_key_header",
                "",
            ),
            "api_key_env_var": analysis_result.get(
                "api_key_env_var",
                "",
            ),
            "http_method": analysis_result.get(
                "http_method",
                "GET",
            ),
            "response_root": analysis_result.get(
                "response_root",
                "",
            ),
        }

        config_path.write_text(
            json.dumps(config, indent=4),
            encoding="utf-8",
        )

        return str(config_path)

    def _generate_mapping_file(
        self,
        folder: Path,
        analysis_result: Dict,
    ) -> str:
        """
        Generate mapping.json from suggested API mapping.
        """

        mapping_path = folder / "mapping.json"

        mapping = {
            "source_type": "rest_api",
            "target_system": "Modula WMS",
            "response_root": analysis_result.get(
                "response_root",
                "",
            ),
            "suggested_mapping": analysis_result.get(
                "suggested_mapping",
                {},
            ),
            "confidence": analysis_result.get(
                "confidence",
                {},
            ),
            "notes": analysis_result.get(
                "notes",
                [],
            ),
        }

        mapping_path.write_text(
            json.dumps(mapping, indent=4),
            encoding="utf-8",
        )

        return str(mapping_path)

    def _generate_readme(
        self,
        folder: Path,
        analysis_result: Dict,
        mapping_path: str,
    ) -> None:
        """
        Generate integration README.
        """

        readme_path = folder / "README.md"

        readme_path.write_text(
            f"""
# Generated API Integration

Customer:
{analysis_result.get("customer_name")}

Base URL:
{analysis_result.get("base_url")}

Orders Endpoint:
{analysis_result.get("orders_endpoint")}

Authentication:
{analysis_result.get("auth_type")}

Response Root:
{analysis_result.get("response_root")}

Mapping File:
{mapping_path}

Generated Files:
- config.json
- api_client.py
- runner.py
- mapping.json
""",
            encoding="utf-8",
        )