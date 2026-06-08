"""
==================================================
API Validation Pipeline Test
==================================================
"""

import json

from src.connectors.api_response_mapper import (
    ApiResponseMapper,
)

from src.validation.validation_manager import (
    ValidationManager,
)


api_response = {
    "orders": [
        {
            "orderNo": "ORD-1001",
            "description": "Customer order",
            "type": "PICK",
            "items": [
                {
                    "sku": "ABC123",
                    "qty": 5,
                }
            ],
        }
    ]
}

with open(
    "generated_integrations/demo_erp/mapping.json",
    "r",
    encoding="utf-8",
) as file:
    mapping_config = json.load(file)

mapper = ApiResponseMapper()

orders = mapper.map_response(
    api_response,
    mapping_config,
)

validation_manager = ValidationManager()

result = validation_manager.validate_orders(
    orders
)

print(result)