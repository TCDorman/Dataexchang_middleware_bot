"""
==================================================
REST API Connector Test
==================================================
"""

from src.connectors.rest_api_connector import (
    RestApiConnector,
)

connector = RestApiConnector(
    "configs/rest/demo_api_config.json"
)

print("Connector Loaded Successfully")
print(connector.config)