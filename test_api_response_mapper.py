"""
==================================================
API Response Mapper Test
==================================================
"""

# ==================================================
# Imports
# ==================================================

from src.connectors.api_response_mapper import (
    ApiResponseMapper,
)


# ==================================================
# Test Data
# ==================================================

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

mapping_config = {
    "response_root": "orders",
    "suggested_mapping": {
        "order_number": "orderNo",
        "description": "description",
        "operation_type": "type",
        "lines": {
            "item_code": "sku",
            "quantity": "qty",
        },
    },
}


# ==================================================
# Run Test
# ==================================================

mapper = ApiResponseMapper()

orders = mapper.map_response(
    api_response,
    mapping_config,
)

print(orders)