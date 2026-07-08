"""
data_quality_checker.py

Data quality checking for transformed order data.

Business rules decide whether an order is allowed to continue.
Data quality checks look for suspicious, incomplete, or duplicate data
that may not always block processing but should be reported.
"""

from typing import Any, Dict, List, Set


class DataQualityChecker:
    """
    Checks transformed orders for common data quality problems.

    Examples:
        - Duplicate order IDs
        - Missing customer names
        - Missing item/part numbers
        - Suspiciously large quantities
    """

    def check_orders(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run all data quality checks against a list of orders.

        Args:
            orders: List of transformed order dictionaries.

        Returns:
            Dictionary containing errors, warnings, and a quality score.
        """

        errors = []
        warnings = []

        errors.extend(self._check_duplicate_order_ids(orders))
        warnings.extend(self._check_missing_customer_info(orders))
        warnings.extend(self._check_missing_part_numbers(orders))
        warnings.extend(self._check_suspicious_quantities(orders))

        quality_score = self._calculate_quality_score(
            total_orders=len(orders),
            error_count=len(errors),
            warning_count=len(warnings),
        )

        return {
            "errors": errors,
            "warnings": warnings,
            "quality_score": quality_score,
        }

    def _check_duplicate_order_ids(self, orders: List[Dict[str, Any]]) -> List[str]:
        """
        Check for duplicate order IDs.

        Duplicate order IDs are treated as errors because they can cause
        overwrites, duplicate shipments, or rejected WMS imports.
        """

        errors = []
        seen_order_ids: Set[str] = set()

        for order in orders:
            order_id = order.get("order_id") or order.get("OrderID")

            if not order_id:
                continue

            if order_id in seen_order_ids:
                errors.append(f"Duplicate order ID found: {order_id}")
            else:
                seen_order_ids.add(order_id)

        return errors

    def _check_missing_customer_info(self, orders: List[Dict[str, Any]]) -> List[str]:
        """
        Check whether basic customer information is missing.

        Missing customer information may not always block a WMS import,
        but it should be visible to the user.
        """

        warnings = []

        for order in orders:
            order_id = order.get("order_id") or order.get("OrderID") or "UNKNOWN"

            customer_name = (
                order.get("customer_name")
                or order.get("CustomerName")
                or order.get("customer")
            )

            if not customer_name:
                warnings.append(
                    f"Order {order_id} is missing customer name information."
                )

        return warnings

    def _check_missing_part_numbers(self, orders: List[Dict[str, Any]]) -> List[str]:
        """
        Check whether each line item has an item/part number.

        Missing part numbers usually make fulfillment impossible, so this
        is reported as a warning for now. Later we may promote it to an error.
        """

        warnings = []

        for order in orders:
            order_id = order.get("order_id") or order.get("OrderID") or "UNKNOWN"
            lines = order.get("lines") or order.get("Lines") or []

            for index, line in enumerate(lines):
                item = (
                    line.get("item")
                    or line.get("Item")
                    or line.get("part_number")
                    or line.get("PartNumber")
                    or line.get("sku")
                )

                if not item:
                    warnings.append(
                        f"Order {order_id}, line {index + 1} is missing an item/part number."
                    )

        return warnings

    def _check_suspicious_quantities(self, orders: List[Dict[str, Any]]) -> List[str]:
        """
        Check for unusually large quantities.

        This does not automatically mean the order is invalid, but it may
        indicate bad input data, unit mismatch, or an accidental extra zero.
        """

        warnings = []

        for order in orders:
            order_id = order.get("order_id") or order.get("OrderID") or "UNKNOWN"
            lines = order.get("lines") or order.get("Lines") or []

            for index, line in enumerate(lines):
                quantity = line.get("quantity") or line.get("Quantity") or line.get("qty")

                try:
                    quantity_value = float(quantity)
                except (TypeError, ValueError):
                    continue

                if quantity_value > 10000:
                    warnings.append(
                        f"Order {order_id}, line {index + 1} has a suspiciously large quantity: {quantity}."
                    )

        return warnings

    def _calculate_quality_score(
        self,
        total_orders: int,
        error_count: int,
        warning_count: int,
    ) -> int:
        """
        Calculate a simple quality score from 0 to 100.

        Errors reduce the score more heavily than warnings.
        """

        if total_orders == 0:
            return 0

        score = 100

        score -= error_count * 25
        score -= warning_count * 5

        return max(score, 0)