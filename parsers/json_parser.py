import sys
from pathlib import Path
import json

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models.wms_models import WMSOrder, WMSOrderLine


def parse_customer_orders_json(file_path: str):
    with open(file_path, "r") as file:
        data = json.load(file)

    orders = []

    for order_data in data["orders"]:
        lines = []

        for line_data in order_data["lines"]:
            line = WMSOrderLine(
                order_number=order_data["order_number"],
                item_code=line_data["item_code"],
                quantity=float(line_data["quantity"]),
            )
            lines.append(line)

        order = WMSOrder(
            order_number=order_data["order_number"],
            description=order_data.get("description"),
            operation_type=order_data.get("operation_type", "P"),
            lines=lines,
        )

        orders.append(order)

    return orders


if __name__ == "__main__":
    orders = parse_customer_orders_json(
        "data/sample_files/customer_orders.json"
    )

    print("\nCUSTOMER JSON ORDERS")
    for order in orders:
        print(order)