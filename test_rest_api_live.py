"""
==================================================
REST API Live Test
==================================================
"""

from src.connectors.rest_api_connector import (
    RestApiConnector,
)

connector = RestApiConnector(
    "configs/rest/demo_api_config.json"
)

print("Base URL:")
print(connector.base_url)

print("\nHeaders:")
print(connector._build_headers())