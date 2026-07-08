from typing import Any, Dict
from src.validation.business_rule_engine import RuleResult


def order_has_id(order: Dict[str, Any]) -> RuleResult:
    order_id = order.get("order_id") or order.get("OrderID")

    if order_id:
        return RuleResult("order_has_id", True, "Order has an ID.")

    return RuleResult("order_has_id", False, "Order is missing an order ID.")


def order_has_lines(order: Dict[str, Any]) -> RuleResult:
    lines = order.get("lines") or order.get("Lines") or []

    if len(lines) > 0:
        return RuleResult("order_has_lines", True, "Order has line items.")

    return RuleResult("order_has_lines", False, "Order must have at least one line item.")


def quantities_are_positive(order: Dict[str, Any]) -> RuleResult:
    lines = order.get("lines") or order.get("Lines") or []

    for index, line in enumerate(lines):
        quantity = line.get("quantity") or line.get("Quantity") or line.get("qty")

        try:
            if float(quantity) <= 0:
                return RuleResult(
                    "quantities_are_positive",
                    False,
                    f"Line {index + 1} has invalid quantity: {quantity}",
                )
        except (TypeError, ValueError):
            return RuleResult(
                "quantities_are_positive",
                False,
                f"Line {index + 1} has non-numeric quantity: {quantity}",
            )

    return RuleResult("quantities_are_positive", True, "All quantities are positive.")