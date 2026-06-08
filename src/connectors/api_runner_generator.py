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
    - Generate working runner.py
"""

# ==================================================
# Imports
# ==================================================

import json
from pathlib import Path
from typing import Dict


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
            folder
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

from src.connectors.rest_api_connector import RestApiConnector


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
        Fetch orders from the configured API endpoint.
        """

        return self.connector.get(endpoint)
''',
            encoding="utf-8",
        )

        return str(api_client_path)

    def _generate_runner(
        self,
        folder: Path,
    ) -> str:
        """
        Generate runner.py.
        """

        runner_path = folder / "runner.py"

        runner_path.write_text(
            '''"""
Generated API Runner

Purpose:
    Runs the generated customer API integration.
"""

# ==================================================
# Imports
# ==================================================

import json
from pathlib import Path

from api_client import GeneratedApiClient


# ==================================================
# Helpers
# ==================================================

def load_config():
    """
    Load package config.json.
    """

    config_path = Path(__file__).parent / "config.json"

    with open(
        config_path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# ==================================================
# Main Runner
# ==================================================

def main():
    """
    Fetch orders from customer API.
    """

    config = load_config()

    client = GeneratedApiClient(
        config["api_config_path"]
    )

    orders_response = client.fetch_orders(
        config["orders_endpoint"]
    )

    print("API RESPONSE")
    print(json.dumps(orders_response, indent=4))


if __name__ == "__main__":
    main()
''',
            encoding="utf-8",
        )

        return str(runner_path)