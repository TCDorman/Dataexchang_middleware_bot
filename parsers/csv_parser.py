import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models.wms_models import WMSItem, WMSOrder, WMSOrderLine


def get_first_value(row, possible_columns, default=None):
    for column in possible_columns:
        if column in row.index and pd.notna(row[column]):
            return str(row[column]).strip()
    return default


def parse_customer_inventory_csv(file_path: str):
    df = pd.read_csv(file_path)
    items = []

    for _, row in df.iterrows():
        item = WMSItem(
            item_code=get_first_value(row, ["sku", "item_code", "material_code"]),
            description=get_first_value(row, ["description", "item_description", "material_description"]),
        )
        items.append(item)

    return items


def parse_customer_orders_csv(header_file_path: str, line_file_path: str):
    header_df = pd.read_csv(header_file_path)
    line_df = pd.read_csv(line_file_path)

    orders = []

    for _, header in header_df.iterrows():
        order_number = get_first_value(header, ["ORD_ORDINE"])

        matching_lines = line_df[line_df["RIG_ORDINE"] == order_number]

        lines = []

        for _, row in matching_lines.iterrows():
            lines.append(
                WMSOrderLine(
                    order_number=get_first_value(row, ["RIG_ORDINE"]),
                    item_code=get_first_value(row, ["RIG_ARTICOLO"]),
                    quantity=float(get_first_value(row, ["RIG_QTAR"], default=0)),
                )
            )

        orders.append(
            WMSOrder(
                order_number=order_number,
                description=get_first_value(header, ["ORD_DES"]),
                operation_type=get_first_value(header, ["ORD_TIPOOP"], default="P"),
                lines=lines,
            )
        )

    return orders


def parse_erp_orders_csv(header_file_path: str, line_file_path: str):
    header_df = pd.read_csv(header_file_path)
    line_df = pd.read_csv(line_file_path)

    orders = []

    header_order_fields = [
        "sales_order_id",
        "order_number",
        "po_num",
        "order_id",
        "client_order_ref",
    ]

    line_order_fields = [
        "sales_order_id",
        "order_number",
        "po_ref",
        "order_id",
        "client_order_ref",
    ]

    item_fields = [
        "product_sku",
        "item_code",
        "part_no",
        "sku",
        "material_code",
    ]

    quantity_fields = [
        "ordered_qty",
        "quantity",
        "qty_requested",
        "qty",
        "requested_quantity",
    ]

    for _, header in header_df.iterrows():
        order_number = get_first_value(header, header_order_fields)

        if not order_number:
            raise ValueError(
                f"Could not find order number in header file. Available columns: {list(header_df.columns)}"
            )

        description = get_first_value(
            header,
            ["customer_name", "description", "buyer", "company_name"],
            default=f"Order {order_number}",
        )

        operation_type = get_first_value(
            header,
            ["operation_type", "order_type", "fulfillment_mode", "process_type"],
            default="P",
        )

        if operation_type.upper() == "PICK":
            operation_type = "P"

        lines = []

        for _, row in line_df.iterrows():
            line_order_number = get_first_value(row, line_order_fields)

            if line_order_number != order_number:
                continue

            item_code = get_first_value(row, item_fields)
            quantity = get_first_value(row, quantity_fields, default=0)

            if not item_code:
                raise ValueError(
                    f"Could not find item code in line file. Available columns: {list(line_df.columns)}"
                )

            lines.append(
                WMSOrderLine(
                    order_number=order_number,
                    item_code=item_code,
                    quantity=float(quantity),
                )
            )

        orders.append(
            WMSOrder(
                order_number=order_number,
                description=description,
                operation_type=operation_type,
                lines=lines,
            )
        )

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
        "data/sample_files/customer_order_headers.csv",
        "data/sample_files/customer_order_lines.csv",
    )

    for order in orders:
        print(order)