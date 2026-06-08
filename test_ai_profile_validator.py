"""
==================================================
AI Profile Validator Test
==================================================

Purpose:
    Tests validation of AI-generated customer profiles.

Location:
    This test assumes ai_profile_validator.py is located in:

        src/validation/ai_profile_validator.py
"""

# ==================================================
# Imports
# ==================================================

from src.validation.ai_profile_validator import AIProfileValidator


# ==================================================
# Test Valid Profile
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
        "Customer": "customer_name",
        "PartNumber": "item",
        "Qty": "quantity",
    },
    "mapping_confidence": {
        "OrderNumber": 98,
        "Customer": 95,
        "PartNumber": 92,
        "Qty": 99,
    },
    "mapping_notes": {
        "OrderNumber": "Clearly represents the order identifier.",
        "Customer": "Clearly represents the customer name.",
        "PartNumber": "Represents the item or SKU.",
        "Qty": "Common abbreviation for quantity.",
    },
}

validator = AIProfileValidator()

result = validator.validate_profile(profile)

print(result)


# ==================================================
# Result Check
# ==================================================

if result["is_valid"]:
    print("\nAI profile validation passed.")
else:
    print("\nAI profile validation failed.")
    print("Errors:")
    for error in result["errors"]:
        print(f"  - {error}")

    print("Warnings:")
    for warning in result["warnings"]:
        print(f"  - {warning}")