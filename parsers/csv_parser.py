import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models.wms_models import WMSItem


def parse_customer_inventory_csv(file_path: str):
    df = pd.read_csv(file_path)

    items = []

    for _, row in df.iterrows():
        item = WMSItem(
            item_code=row["sku"],
            description=row["description"]
        )

        items.append(item)

    return items


if __name__ == "__main__":
    items = parse_customer_inventory_csv(
        "data/sample_files/customer_inventory.csv"
    )

    for item in items:
        print(item)

from models.wms_models import WMSOrder, WMSOrderLine


def parse_customer_orders_csv(file_path: str):
    df = pd.read_csv(file_path)

    grouped_orders = {}

    for _, row in df.iterrows():
        order_number = row["order_number"]

        if order_number not in grouped_orders:
            grouped_orders[order_number] = []

        line = WMSOrderLine(
            order_number=order_number,
            item_code=row["item_code"],
            quantity=float(row["quantity"]),
        )

        grouped_orders[order_number].append(line)

    orders = []

    for order_number, lines in grouped_orders.items():
        order = WMSOrder(
            order_number=order_number,
            description=f"Customer Order {order_number}",
            operation_type="P",
            lines=lines,
        )

        orders.append(order)

    return orders

if __name__ == "__main__":

    print("\nCUSTOMER INVENTORY")
    inventory_items = parse_customer_inventory_csv(
        "data/sample_files/customer_inventory.csv"
    )

    for item in inventory_items:
        print(item)

    print("\nCUSTOMER ORDERS")

    orders = parse_customer_orders_csv(
        "data/sample_files/customer_orders.csv"
    )

    for order in orders:
        print(order)