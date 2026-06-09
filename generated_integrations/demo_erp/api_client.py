"""
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
