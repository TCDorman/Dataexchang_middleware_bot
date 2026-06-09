"""
==================================================
API Connection Tester Test
==================================================
"""

from src.connectors.api_connection_tester import (
    ApiConnectionTester,
)

tester = ApiConnectionTester()

result = tester.test_connection(
    "configs/rest/demo_erp_api.json"
)

print(result)