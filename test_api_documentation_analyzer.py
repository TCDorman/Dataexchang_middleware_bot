"""
==================================================
API Documentation Analyzer Test
==================================================
"""

# ==================================================
# Imports
# ==================================================

from src.connectors.api_documentation_analyzer import (
    ApiDocumentationAnalyzer,
)


# ==================================================
# Sample API Documentation
# ==================================================

documentation = """
Customer: Demo ERP

Base URL:
https://api.demo-erp.com/v1

Authentication:
Use an API key in the Authorization header.

Orders Endpoint:
GET /orders

Sample Response:
{
    "orders": [
        {
            "orderNo": "ORD-1001",
            "description": "Customer order",
            "type": "PICK",
            "items": [
                {
                    "sku": "ABC123",
                    "qty": 5
                }
            ]
        }
    ]
}
"""


# ==================================================
# Run Test
# ==================================================

analyzer = ApiDocumentationAnalyzer()

result = analyzer.analyze_documentation(documentation)

print(result)