"""
==================================================
REST API Connector
==================================================

Purpose:
    Provides a reusable REST API client for customer
    integrations.

Responsibilities:
    - Load API configuration
    - Build authentication headers
    - Execute GET requests
    - Execute POST requests
    - Return JSON responses
"""

# ==================================================
# Imports
# ==================================================

import json
import os
from typing import Dict, Optional

import requests


# ==================================================
# REST API Connector
# ==================================================

class RestApiConnector:
    """
    Generic REST API connector.
    """

    def __init__(
        self,
        config_path: str,
    ):
        """
        Initialize connector using a config file.
        """

        self.config = self._load_config(
            config_path
        )

        self.base_url = self.config["base_url"]

    def get(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
    ) -> Dict:
        """
        Execute GET request.
        """

        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers=self._build_headers(),
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def post(
        self,
        endpoint: str,
        payload: Dict,
    ) -> Dict:
        """
        Execute POST request.
        """

        response = requests.post(
            f"{self.base_url}{endpoint}",
            headers=self._build_headers(),
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def _build_headers(
        self,
    ) -> Dict:
        """
        Build authentication headers.
        """

        auth_type = self.config.get(
            "auth_type",
            "api_key",
        )

        if auth_type == "api_key":
            api_key = os.getenv(
                self.config["api_key_env_var"]
            )

            if not api_key:
                raise ValueError(
                    "Missing API key environment variable: "
                    f"{self.config['api_key_env_var']}"
                )

            return {
                self.config["api_key_header"]: api_key
            }

        return {}

    def _load_config(
        self,
        config_path: str,
    ) -> Dict:
        """
        Load JSON API configuration.
        """

        with open(
            config_path,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)