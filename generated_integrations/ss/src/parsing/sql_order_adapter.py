"""
sql_order_adapter.py

Adapts parsed SQL dictionary orders into WMSOrder objects
used by the Modula XML exporter.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models.wms_models import WMSOrder, WMSOrderLine


def convert_sql_orders_to_wms_orders(sql_orders: list[dict]) -> list[WMSOrder]:
    wms_orders = []

    for sql_order in sql_orders:
        order_number = str(sql_order.get("order_id", ""))

        lines = []

        for sql_line in sql_order.get("lines", []):
            line = WMSOrderLine(
                order_number=order_number,
                item_code=str(sql_line.get("item", "")),
                quantity=sql_line.get("quantity", 0),
                sub1="",
                sub2="",
            )

            lines.append(line)

        order = WMSOrder(
            order_number=order_number,
            description=sql_order.get("customer_name") or "",
            operation_type="P",
            lines=lines,
        )

        wms_orders.append(order)

    return wms_orders