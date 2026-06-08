"""
==================================================
Validation Manager
==================================================

Purpose:
    Central validation entry point for the Modula
    Integration Agent.

Responsibilities:
    - Validate AI-generated customer profiles
    - Validate normalized order data
    - Combine validation results into one standard format
"""

# ==================================================
# Imports
# ==================================================

from typing import Any, Dict, List

from src.validation.ai_profile_validator import AIProfileValidator
from src.validation.business_rule_validator import BusinessRuleValidator
from src.validation.duplicate_detector import DuplicateDetector


# ==================================================
# Validation Manager
# ==================================================

class ValidationManager:
    """
    Coordinates all validation checks.
    """

    def __init__(self):
        """
        Initialize validation components.
        """

        self.ai_profile_validator = AIProfileValidator()
        self.duplicate_detector = DuplicateDetector()
        self.business_rule_validator = BusinessRuleValidator()

    def validate_profile(
        self,
        profile: Dict,
    ) -> Dict:
        """
        Validate an AI-generated customer profile.
        """

        result = self.ai_profile_validator.validate_profile(profile)

        return {
            "validation_type": "profile",
            "is_valid": result["is_valid"],
            "errors": result["errors"],
            "warnings": result["warnings"],
            "details": result,
        }

    def validate_orders(
        self,
        orders: List[Any],
    ) -> Dict:
        """
        Validate normalized orders before export.
        """

        duplicate_result = self.duplicate_detector.detect_duplicates(
            orders
        )

        business_rule_result = (
            self.business_rule_validator.validate_orders(
                orders
            )
        )

        errors = []
        warnings = []

        if duplicate_result["duplicate_order_ids"]:
            errors.append(
                "Duplicate order IDs detected: "
                f"{duplicate_result['duplicate_order_ids']}"
            )

        if duplicate_result["duplicate_lines"]:
            warnings.append(
                "Duplicate order lines detected: "
                f"{duplicate_result['duplicate_lines']}"
            )

        errors.extend(
            business_rule_result["errors"]
        )

        warnings.extend(
            business_rule_result["warnings"]
        )

        return {
            "validation_type": "orders",
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "details": {
                "duplicate_check": duplicate_result,
                "business_rule_check": business_rule_result,
            },
        }