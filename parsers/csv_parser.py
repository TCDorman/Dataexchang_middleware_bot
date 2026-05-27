import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models.wms_models import WMSItem, WMSOrder, WMSOrderLine


def parse_customer_inventory_csv(file_path: str):
    df = pd.read_csv(file_path)
    items = []

    for _, row in df.iterrows():
        items.append(
            WMSItem(
                item_code=row["sku"],
                description=row["description"],
            )
        )

    return items


def parse_customer_orders_csv(header_file_path: str, line_file_path: str):
    header_df = pd.read_csv(header_file_path)
    line_df = pd.read_csv(line_file_path)

    orders = []

    for _, header in header_df.iterrows():
        order_number = header["ORD_ORDINE"]
        matching_lines = line_df[line_df["RIG_ORDINE"] == order_number]

        lines = []

        for _, row in matching_lines.iterrows():
            lines.append(
                WMSOrderLine(
                    order_number=row["RIG_ORDINE"],
                    item_code=row["RIG_ARTICOLO"],
                    quantity=float(row["RIG_QTAR"]),
                )
            )

        orders.append(
            WMSOrder(
                order_number=order_number,
                description=header["ORD_DES"],
                operation_type=header["ORD_TIPOOP"],
                lines=lines,
            )
        )

    return orders


if __name__ == "__main__":
    print("\nCUSTOMER INVENTORY")
    for item in parse_customer_inventory_csv("data/sample_files/customer_inventory.csv"):
        print(item)

    print("\nCUSTOMER ORDERS")
    orders = parse_customer_orders_csv(
        "data/sample_files/customer_order_headers.csv",
        "data/sample_files/customer_order_lines.csv",
    )

    for order in orders:
        print(order)

def parse_erp_orders_csv(header_file_path: str, line_file_path: str):
    header_df = pd.read_csv(header_file_path)
    line_df = pd.read_csv(line_file_path)

    orders = []

    for _, header in header_df.iterrows():
        order_number = header["sales_order_id"]
        matching_lines = line_df[line_df["sales_order_id"] == order_number]

        lines = []

        for _, row in matching_lines.iterrows():
            lines.append(
                WMSOrderLine(
                    order_number=order_number,
                    item_code=row["product_sku"],
                    quantity=float(row["ordered_qty"]),
                )
            )

        orders.append(
            WMSOrder(
                order_number=order_number,
                description=f"{header['customer_name']} - {header['requested_ship_date']}",
                operation_type="P",
                lines=lines,
            )
        )

    return orders