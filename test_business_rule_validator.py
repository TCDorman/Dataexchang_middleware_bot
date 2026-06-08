"""
==================================================
Business Rule Validator Test
==================================================

Purpose:
    Tests order-level business rule validation.
"""

# ==================================================
# Imports
# ==================================================

from src.validation.business_rule_validator import BusinessRuleValidator


# ==================================================
# Test Data
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
                "item": "",
                "quantity": -2,
            },
        ],
    },
    {
        "order_id": "",
        "customer_name": "Ford",
        "lines": [],
    },
]


# ==================================================
# Run Test
# ==================================================

validator = BusinessRuleValidator()

result = validator.validate_orders(orders)

print(result)