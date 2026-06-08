"""
==================================================
Validation Manager Test
==================================================

Purpose:
    Tests centralized validation for profiles and orders.
"""

# ==================================================
# Imports
# ==================================================

from src.validation.validation_manager import ValidationManager


# ==================================================
# Test Profile Validation
# ==================================================

profile = {
    "customer_name": "Test Customer",
    "header_signature": [
        "OrderNumber",
        "Customer",
        "PartNumber",
        "Qty",
    ],
    "field_mapping": {
        "OrderNumber": "order_id",
    },
    "mapping_confidence": {
        "OrderNumber": 95,
    },
    "mapping_notes": {
        "OrderNumber": "Clearly represents order ID.",
    },
}


# ==================================================
# Test Order Validation
# ==================================================

orders = [
    {
        "order_id": "ORD-1001",
        "customer_name": "Ford",
        "lines": [
            {
                "item": "ABC123",
                "quantity": 5,
            },
            {
                "item": "ABC123",
                "quantity": 5,
            },
        ],
    },
    {
        "order_id": "ORD-1001",
        "customer_name": "Ford",
        "lines": [
            {
                "item": "XYZ789",
                "quantity": 2,
            },
        ],
    },
]


# ==================================================
# Run Test
# ==================================================

manager = ValidationManager()

profile_result = manager.validate_profile(profile)
order_result = manager.validate_orders(orders)

print("\nPROFILE VALIDATION RESULT")
print(profile_result)

print("\nORDER VALIDATION RESULT")
print(order_result)