"""
==================================================
API Runner Generator
==================================================

Purpose:
    Generates runnable starter files for customer
    REST API integration packages.

Responsibilities:
    - Generate package-level config.json
    - Generate working api_client.py
    - Generate executable runner.py
"""

# ==================================================
# Imports
# ==================================================

import json
from pathlib import Path
from typing import Dict

from src.connectors.generated_runner_builder import (
    GeneratedRunnerBuilder,
)


# ==================================================
# API Runner Generator
# ==================================================

class ApiRunnerGenerator:
    """
    Generates runnable API integration starter files.
    """

    def generate_runner_files(
        self,
        folder: Path,
        customer_name: str,
        analysis_result: Dict,
        api_config_path: str,
    ) -> Dict:
        """
        Generate runnable files for the API package.
        """

        config_path = self._generate_package_config(
            folder,
            customer_name,
            analysis_result,
            api_config_path,
        )

        api_client_path = self._generate_api_client(
            folder
        )

        runner_path = self._generate_runner(
            folder,
            customer_name,
            analysis_result,
        )

        return {
            "config_path": config_path,
            "api_client_path": api_client_path,
            "runner_path": runner_path,
        }

    def _generate_package_config(
        self,
        folder: Path,
        customer_name: str,
        analysis_result: Dict,
        api_config_path: str,
    ) -> str:
        """
        Generate package config.json.
        """

        config_path = folder / "config.json"

        config = {
            "customer_name": customer_name,
            "api_config_path": api_config_path,
            "orders_endpoint": analysis_result.get(
                "orders_endpoint",
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
            "mapping_file": "mapping.json",
        }

        config_path.write_text(
            json.dumps(config, indent=4),
            encoding="utf-8",
        )

        return str(config_path)

    def _generate_api_client(
        self,
        folder: Path,
    ) -> str:
        """
        Generate api_client.py.
        """

        api_client_path = folder / "api_client.py"

        api_client_path.write_text(
            '''"""
Generated API Client

Purpose:
    Uses the shared RestApiConnector to fetch customer
    order data from a configured REST API.
"""

# ==================================================
# Imports
# ==================================================

from src.connectors.rest_api_connector import (
    RestApiConnector,
)


# ==================================================
# Generated API Client
# ==================================================

class GeneratedApiClient:
    """
    Customer-specific API client.
    """

    def __init__(
        self,
        api_config_path: str,
    ):
        """
        Initialize connector.
        """

        self.connector = RestApiConnector(
            api_config_path
        )

    def fetch_orders(
        self,
        endpoint: str,
    ):
        """
        Fetch orders from customer API.
        """

        return self.connector.get(
            endpoint
        )
''',
            encoding="utf-8",
        )

        return str(api_client_path)

    def _generate_runner(
        self,
        folder: Path,
        customer_name: str,
        analysis_result: Dict,
    ) -> str:
        """
        Generate executable runner.py.
        """

        runner_builder = GeneratedRunnerBuilder()

        return runner_builder.build_runner(
            folder=folder,
            customer_name=customer_name,
            analysis_result=analysis_result,
        )