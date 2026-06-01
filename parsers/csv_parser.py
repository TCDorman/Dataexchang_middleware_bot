import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models.wms_models import WMSItem, WMSOrder, WMSOrderLine


def find_column(columns, possible_names):
    for name in possible_names:
        if name in columns:
            return name
    return None


def parse_customer_inventory_csv(file_path: str):
    df = pd.read_csv(file_path)

    item_field = find_column(
        df.columns,
        ["sku", "item_code", "material_code", "part_no", "ART_ARTICOLO"],
    )

    description_field = find_column(
        df.columns,
        ["description", "item_description", "material_description", "item_name", "ART_DES"],
    )

    if not item_field:
        raise ValueError(f"Could not detect item field. Columns: {list(df.columns)}")

    items = []

    for _, row in df.iterrows():
        items.append(
            WMSItem(
                item_code=str(row[item_field]),
                description=str(row[description_field]) if description_field else "",
            )
        )

    return items


def parse_erp_orders_csv(header_file_path: str, line_file_path: str):
    header_df = pd.read_csv(header_file_path)
    line_df = pd.read_csv(line_file_path)

    header_order_field = find_column(
        header_df.columns,
        ["ORD_ORDINE", "sales_order_id", "order_number", "client_order_ref", "po_num", "order_id"],
    )

    description_field = find_column(
        header_df.columns,
        ["ORD_DES", "customer_name", "description", "company_name", "buyer"],
    )

    operation_field = find_column(
        header_df.columns,
        ["ORD_TIPOOP", "operation_type", "process_type", "fulfillment_mode", "order_type"],
    )

    line_order_field = find_column(
        line_df.columns,
        ["RIG_ORDINE", "sales_order_id", "order_number", "client_order_ref", "po_ref", "order_id"],
    )

    item_field = find_column(
        line_df.columns,
        ["RIG_ARTICOLO", "sku", "item_code", "material_code", "part_no", "product_sku"],
    )

    quantity_field = find_column(
        line_df.columns,
        ["RIG_QTAR", "quantity", "qty", "requested_quantity", "qty_requested", "ordered_qty"],
    )

    if not header_order_field:
        raise ValueError(f"Could not detect header order field. Header columns: {list(header_df.columns)}")

    if not line_order_field:
        raise ValueError(f"Could not detect line order field. Line columns: {list(line_df.columns)}")

    if not item_field:
        raise ValueError(f"Could not detect item field. Line columns: {list(line_df.columns)}")

    if not quantity_field:
        raise ValueError(f"Could not detect quantity field. Line columns: {list(line_df.columns)}")

    orders = []

    for _, header in header_df.iterrows():
        order_number = str(header[header_order_field])

        matching_lines = line_df[
            line_df[line_order_field].astype(str) == order_number
        ]

        lines = []

        for _, row in matching_lines.iterrows():
            lines.append(
                WMSOrderLine(
                    order_number=order_number,
                    item_code=str(row[item_field]),
                    quantity=float(row[quantity_field]),
                )
            )

        description = (
            str(header[description_field])
            if description_field
            else f"Order {order_number}"
        )

        operation_type = (
            str(header[operation_field])
            if operation_field
            else "P"
        )

        if operation_type.upper() == "PICK":
            operation_type = "P"

        orders.append(
            WMSOrder(
                order_number=order_number,
                description=description,
                operation_type=operation_type,
                lines=lines,
            )
        )

    return orders


def parse_customer_orders_csv(header_file_path: str, line_file_path: str):
    return parse_erp_orders_csv(header_file_path, line_file_path)


if __name__ == "__main__":
    orders = parse_erp_orders_csv(
        "data/sample_files/test_ui_headers.csv",
        "data/sample_files/test_ui_lines.csv",
    )

    for order in orders:
        print(order)