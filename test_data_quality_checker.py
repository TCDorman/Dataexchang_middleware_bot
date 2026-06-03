"""
test_data_quality_checker.py

Temporary manual test for the DataQualityChecker.

This verifies that duplicate IDs, missing fields, and suspicious
quantities are detected correctly.
"""

from src.validation.data_quality_checker import DataQualityChecker


checker = DataQualityChecker()

orders = [
    {
        "order_id": "ORD-1001",
        "customer_name": "Ford",
        "lines": [
            {"item": "ABC123", "quantity": 5},
            {"item": "XYZ789", "quantity": 15000},
        ],
    },
    {
        "order_id": "ORD-1001",
        "lines": [
            {"quantity": 2},
        ],
    },
]

result = checker.check_orders(orders)

print(result)