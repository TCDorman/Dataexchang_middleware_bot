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

    def validate_profile(
        self,
        profile: Dict,
    ) -> Dict:
        """
        Validate an AI-generated customer profile.

        Args:
            profile:
                AI-generated profile dictionary.

        Returns:
            Standard validation result.
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

        Args:
            orders:
                List of normalized order objects or dictionaries.

        Returns:
            Standard validation result.
        """

        duplicate_result = self.duplicate_detector.detect_duplicates(
            orders
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

        return {
            "validation_type": "orders",
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "details": {
                "duplicate_check": duplicate_result,
            },
        }