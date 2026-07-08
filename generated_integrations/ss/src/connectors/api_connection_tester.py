"""
==================================================
API Connection Tester
==================================================

Purpose:
    Tests generated REST API configurations before
    using them in production integrations.

Responsibilities:
    - Load API configuration
    - Test configured endpoint
    - Detect authentication/configuration issues
    - Return structured test results
"""

# ==================================================
# Imports
# ==================================================

import json
from typing import Dict

import requests


# ==================================================
# API Connection Tester
# ==================================================

class ApiConnectionTester:
    """
    Tests customer API connectivity.
    """

    def test_connection(
        self,
        config_path: str,
    ) -> Dict:
        """
        Test API connection using a generated config file.
        """

        config = self._load_config(config_path)

        base_url = config.get("base_url", "")
        endpoint = config.get("orders_endpoint", "")
        url = f"{base_url}{endpoint}"

        headers_result = self._build_headers(config)

        if not headers_result["success"]:
            return {
                "connection_success": False,
                "endpoint_reachable": False,
                "auth_valid": False,
                "status_code": None,
                "url": url,
                "error": headers_result["error"],
            }

        try:
            response = requests.get(
                url,
                headers=headers_result["headers"],
                timeout=30,
            )

            return {
                "connection_success": response.ok,
                "endpoint_reachable": response.status_code != 404,
                "auth_valid": response.status_code not in [401, 403],
                "status_code": response.status_code,
                "url": url,
                "sample_response_received": response.ok,
                "error": None if response.ok else response.text,
            }

        except requests.RequestException as error:
            return {
                "connection_success": False,
                "endpoint_reachable": False,
                "auth_valid": False,
                "status_code": None,
                "url": url,
                "sample_response_received": False,
                "error": str(error),
            }

    def _load_config(
        self,
        config_path: str,
    ) -> Dict:
        """
        Load API config JSON.
        """

        with open(
            config_path,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    def _build_headers(
        self,
        config: Dict,
    ) -> Dict:
        """
        Build request headers for connection test.
        """

        auth_type = config.get("auth_type", "none")

        if auth_type in ["none", "unknown", ""]:
            return {
                "success": True,
                "headers": {},
                "error": None,
            }

        if auth_type == "api_key":
            api_key_env_var = config.get("api_key_env_var")

            if not api_key_env_var:
                return {
                    "success": False,
                    "headers": {},
                    "error": "Missing api_key_env_var in config.",
                }

            import os

            api_key = os.getenv(api_key_env_var)

            if not api_key:
                return {
                    "success": False,
                    "headers": {},
                    "error": (
                        "Missing API key environment variable: "
                        f"{api_key_env_var}"
                    ),
                }

            return {
                "success": True,
                "headers": {
                    config.get("api_key_header", "Authorization"): api_key
                },
                "error": None,
            }

        return {
            "success": False,
            "headers": {},
            "error": f"Unsupported auth_type: {auth_type}",
        }