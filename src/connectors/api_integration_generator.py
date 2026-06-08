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
    - Generate starter files
    - Return generation results
"""

# ==================================================
# Imports
# ==================================================

import json
from pathlib import Path
from typing import Dict


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

        Args:
            analysis_result:
                Output from ApiDocumentationAnalyzer.

        Returns:
            Generation result.
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

        self._generate_runner(
            integration_folder,
            customer_name,
        )

        self._generate_api_client(
            integration_folder,
            customer_name,
        )

        self._generate_readme(
            integration_folder,
            analysis_result,
            mapping_path,
        )

        return {
            "status": "success",
            "customer_name": customer_name,
            "integration_folder": str(
                integration_folder
            ),
            "config_path": config_path,
            "mapping_path": mapping_path,
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

    def _generate_runner(
        self,
        folder: Path,
        customer_name: str,
    ):
        """
        Generate starter runner file.
        """

        runner_path = folder / "runner.py"

        runner_path.write_text(
            f'''"""
Generated API Runner
Customer: {customer_name}

Purpose:
    Starter entry point for running this generated
    customer API integration.
"""

print("API integration runner placeholder")
''',
            encoding="utf-8",
        )

    def _generate_api_client(
        self,
        folder: Path,
        customer_name: str,
    ):
        """
        Generate starter API client file.
        """

        client_path = folder / "api_client.py"

        client_path.write_text(
            f'''"""
Generated API Client
Customer: {customer_name}

Purpose:
    Starter client for customer REST API calls.
"""

print("API client placeholder")
''',
            encoding="utf-8",
        )

    def _generate_readme(
        self,
        folder: Path,
        analysis_result: Dict,
        mapping_path: str,
    ):
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
""",
            encoding="utf-8",
        )