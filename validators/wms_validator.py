import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models.wms_models import WMSItem, WMSOrder


def validate_items(items: list[WMSItem]) -> list[str]:
    errors = []

    for index, item in enumerate(items, start=1):
        if not item.item_code:
            errors.append(f"Item {index}: item_code is required")

    return errors


def validate_orders(orders: list[WMSOrder]) -> list[str]:
    errors = []

    for order in orders:
        if not order.order_number:
            errors.append("Order is missing order_number")

        if not order.operation_type:
            errors.append(f"Order {order.order_number}: operation_type is required")

        if not order.lines:
            errors.append(f"Order {order.order_number}: at least one line is required")

        for line_index, line in enumerate(order.lines, start=1):
            if not line.item_code:
                errors.append(
                    f"Order {order.order_number}, line {line_index}: item_code is required"
                )

            if line.quantity <= 0:
                errors.append(
                    f"Order {order.order_number}, line {line_index}: quantity must be greater than 0"
                )

    return errors