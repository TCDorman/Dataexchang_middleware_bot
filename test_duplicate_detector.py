"""
==================================================
Duplicate Detector Test
==================================================

Purpose:
    Tests duplicate order and duplicate line detection.
"""

# ==================================================
# Imports
# ==================================================

from src.validation.duplicate_detector import DuplicateDetector


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
                "item": "ABC123",
                "quantity": 5,
            },
        ],
    },
    {
        "order_id": "ORD-1002",
        "customer_name": "Ford",
        "lines": [
            {
                "item": "XYZ789",
                "quantity": 2,
            },
        ],
    },
    {
        "order_id": "ORD-1001",
        "customer_name": "Ford",
        "lines": [
            {
                "item": "LMN456",
                "quantity": 1,
            },
        ],
    },
]


# ==================================================
# Run Test
# ==================================================

detector = DuplicateDetector()

result = detector.detect_duplicates(orders)

print(result)