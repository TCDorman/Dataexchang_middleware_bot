"""
==================================================
Business Rule Validator
==================================================

Purpose:
    Validates normalized orders against business rules
    before export to Modula WMS.

Responsibilities:
    - Ensure order numbers are present
    - Ensure each order has at least one line
    - Ensure item codes are present
    - Ensure quantities are positive numbers

Supported order formats:
    - Dictionary orders using order_id / item
    - WMSOrder objects using order_number / item_code
"""

# ==================================================
# Imports
# ==================================================

from typing import Any, Dict, List


# ==================================================
# Business Rule Validator
# ==================================================

class BusinessRuleValidator:
    """
    Validates normalized order business rules.
    """

    def validate_orders(
        self,
        orders: List[Any],
    ) -> Dict:
        """
        Validate business rules for normalized orders.

        Args:
            orders:
                List of order dictionaries or WMSOrder objects.

        Returns:
            Validation result dictionary.
        """

        errors = []
        warnings = []

        for index, order in enumerate(orders):
            order_id = self._get_order_id(order)
            lines = self._get_value(order, "lines", [])

            if not order_id:
                errors.append(
                    f"Order at index {index} is missing order_id/order_number."
                )

            if not lines:
                errors.append(
                    f"Order '{order_id}' has no line items."
                )
                continue

            for line_index, line in enumerate(lines):
                item = self._get_line_item(line)
                quantity = self._get_value(line, "quantity")

                if not item:
                    errors.append(
                        f"Order '{order_id}', line {line_index} "
                        "is missing item/item_code."
                    )

                if quantity in [None, ""]:
                    errors.append(
                        f"Order '{order_id}', line {line_index} "
                        "is missing quantity."
                    )
                    continue

                try:
                    numeric_quantity = float(quantity)

                    if numeric_quantity <= 0:
                        errors.append(
                            f"Order '{order_id}', line {line_index} "
                            f"has invalid quantity: {quantity}."
                        )

                except (TypeError, ValueError):
                    errors.append(
                        f"Order '{order_id}', line {line_index} "
                        f"has non-numeric quantity: {quantity}."
                    )

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def _get_order_id(
        self,
        order: Any,
    ):
        """
        Get order identifier from supported order formats.
        """

        return (
            self._get_value(order, "order_id")
            or self._get_value(order, "order_number")
        )

    def _get_line_item(
        self,
        line: Any,
    ):
        """
        Get item identifier from supported line formats.
        """

        return (
            self._get_value(line, "item")
            or self._get_value(line, "item_code")
        )

    def _get_value(
        self,
        obj: Any,
        field_name: str,
        default=None,
    ):
        """
        Read a value from either a dictionary or an object.
        """

        if isinstance(obj, dict):
            return obj.get(field_name, default)

        return getattr(obj, field_name, default)