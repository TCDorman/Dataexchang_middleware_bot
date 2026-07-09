"""
==================================================
API Order Model Adapter
==================================================

Purpose:
    Converts normalized API order dictionaries into
    WMSOrder and WMSOrderLine model objects.
"""

# ==================================================
# Imports
# ==================================================

from typing import Dict, List

from models.wms_models import WMSOrder, WMSOrderLine


# ==================================================
# API Order Model Adapter
# ==================================================

class ApiOrderModelAdapter:
    """
    Converts normalized API orders into WMS models.
    """

    def convert_orders(
        self,
        orders: List[Dict],
    ) -> List[WMSOrder]:
        """
        Convert normalized order dictionaries into WMSOrder objects.
        """

        converted_orders = []

        for order in orders:
            converted_orders.append(
                self._convert_order(order)
            )

        return converted_orders

    def _convert_order(
        self,
        order: Dict,
    ) -> WMSOrder:
        """
        Convert one normalized order dictionary into a WMSOrder.
        """

        order_number = order.get("order_number")

        lines = [
            WMSOrderLine(
                order_number=order_number,
                item_code=line.get("item_code"),
                quantity=line.get("quantity"),
            )
            for line in order.get("lines", [])
        ]

        return WMSOrder(
            order_number=order_number,
            description=order.get("description"),
            operation_type=order.get("operation_type", "PICK"),
            lines=lines,
        )