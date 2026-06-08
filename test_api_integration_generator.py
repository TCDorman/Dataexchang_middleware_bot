"""
==================================================
API Integration Generator Test
==================================================
"""

from src.connectors.api_integration_generator import (
    ApiIntegrationGenerator,
)

analysis_result = {
    "customer_name": "Demo ERP",
    "base_url": "https://api.demo-erp.com/v1",
    "orders_endpoint": "/orders",
    "auth_type": "api_key",
    "api_key_header": "Authorization",
    "api_key_env_var": "DEMO_API_KEY",
}

generator = ApiIntegrationGenerator()

result = generator.generate(
    analysis_result
)

print(result)