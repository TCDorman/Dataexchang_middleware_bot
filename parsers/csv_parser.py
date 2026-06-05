import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.schema_intelligence_agent import infer_mapping_with_samples
from models.wms_models import WMSItem, WMSOrder, WMSOrderLine


# ==================================================
# Fallback Column Finder
# ==================================================
def find_column(columns, possible_names):
    """
    Find a column by checking exact known names.

    This is kept as a safety fallback in case the
    schema intelligence agent cannot confidently detect
    a required field.
    """
    for name in possible_names:
        if name in columns:
            return name

    return None


# ==================================================
# Get Intelligent Mapping
# ==================================================
def get_intelligent_mapping(file_path: str):
    """
    Ask the schema intelligence agent to infer field mappings
    using both column names and sample values.

    Example output:
    {
        "order_id": "PO_NUM",
        "customer_name": "BUYER",
        "item": "PART_NO",
        "quantity": "QTY_REQ"
    }
    """
    mapping_result = infer_mapping_with_samples(file_path)

    return mapping_result["mapping"]


# ==================================================
# Parse Customer Inventory CSV
# ==================================================
def parse_customer_inventory_csv(file_path: str):
    """
    Parse an inventory/item master CSV into WMSItem objects.

    The parser first uses schema intelligence, then falls
    back to exact known column names if needed.
    """
    df = pd.read_csv(file_path)

    mapping = get_intelligent_mapping(file_path)

    item_field = mapping.get("item")

    # Fallback in case schema intelligence cannot detect item.
    if not item_field:
        item_field = find_column(
            df.columns,
            [
                "item",
                "sku",
                "item_code",
                "material_code",
                "part_no",
                "part_number",
                "product_code",
                "ART_ARTICOLO",
            ],
        )

    description_field = find_column(
        df.columns,
        [
            "description",
            "item_description",
            "material_description",
            "item_name",
            "ART_DES",
        ],
    )

    if not item_field:
        raise ValueError(
            f"Could not detect item field. Columns: {list(df.columns)}"
        )

    items = []

    for _, row in df.iterrows():
        items.append(
            WMSItem(
                item_code=str(row[item_field]),
                description=str(row[description_field])
                if description_field
                else "",
            )
        )

    return items


# ==================================================
# Parse Single-File Order CSV
# ==================================================
def parse_single_file_orders_csv(file_path: str):
    """
    Parse a flat customer order CSV into WMSOrder objects.

    Supported shape:
    PO_NUM,BUYER,PART_NO,QTY_REQ
    9001,Ford,ABC123,5
    9001,Ford,XYZ789,2
    9002,Ford,LMN456,10

    The parser groups rows by order_id and turns each row
    into an order line.
    """
    df = pd.read_csv(file_path)

    mapping = get_intelligent_mapping(file_path)

    order_field = mapping.get("order_id")
    customer_field = mapping.get("customer_name")
    item_field = mapping.get("item")
    quantity_field = mapping.get("quantity")
    operation_field = mapping.get("operation_type")

    # ----------------------------------------------
    # Fallbacks for fields that intelligence missed.
    # ----------------------------------------------
    if not order_field:
        order_field = find_column(
            df.columns,
            [
                "ORD_ORDINE",
                "sales_order_id",
                "order_number",
                "client_order_ref",
                "po_num",
                "po_number",
                "order_id",
            ],
        )

    if not customer_field:
        customer_field = find_column(
            df.columns,
            [
                "ORD_DES",
                "customer_name",
                "customer",
                "description",
                "company_name",
                "buyer",
            ],
        )

    if not operation_field:
        operation_field = find_column(
            df.columns,
            [
                "ORD_TIPOOP",
                "operation_type",
                "process_type",
                "fulfillment_mode",
                "order_type",
            ],
        )

    if not item_field:
        item_field = find_column(
            df.columns,
            [
                "RIG_ARTICOLO",
                "item",
                "sku",
                "item_code",
                "material_code",
                "part_no",
                "part_number",
                "product_sku",
                "product_code",
            ],
        )

    if not quantity_field:
        quantity_field = find_column(
            df.columns,
            [
                "RIG_QTAR",
                "quantity",
                "qty",
                "qty_req",
                "requested_quantity",
                "qty_requested",
                "ordered_qty",
            ],
        )

    # ----------------------------------------------
    # Required Field Validation
    # ----------------------------------------------
    if not order_field:
        raise ValueError(
            f"Could not detect order field. Columns: {list(df.columns)}"
        )

    if not item_field:
        raise ValueError(
            f"Could not detect item field. Columns: {list(df.columns)}"
        )

    if not quantity_field:
        raise ValueError(
            f"Could not detect quantity field. Columns: {list(df.columns)}"
        )

    # ----------------------------------------------
    # Build WMS Orders
    # ----------------------------------------------
    orders = []

    grouped_orders = df.groupby(
        df[order_field].astype(str),
        sort=False,
    )

    for order_number, order_rows in grouped_orders:
        first_row = order_rows.iloc[0]

        description = (
            str(first_row[customer_field])
            if customer_field
            else f"Order {order_number}"
        )

        operation_type = (
            str(first_row[operation_field])
            if operation_field
            else "P"
        )

        # Normalize common operation descriptions.
        if operation_type.upper() == "PICK":
            operation_type = "P"

        lines = []

        for _, row in order_rows.iterrows():
            lines.append(
                WMSOrderLine(
                    order_number=str(order_number),
                    item_code=str(row[item_field]),
                    quantity=float(row[quantity_field]),
                )
            )

        orders.append(
            WMSOrder(
                order_number=str(order_number),
                description=description,
                operation_type=operation_type,
                lines=lines,
            )
        )

    return orders


# ==================================================
# Parse Header/Line ERP Orders CSV
# ==================================================
def parse_header_line_orders_csv(
    header_file_path: str,
    line_file_path: str,
):
    """
    Parse separate header and line CSV files into WMSOrder
    objects.

    Supported shape:

    Header file:
    PO_NUM,BUYER

    Line file:
    PO_NUM,PART_NO,QTY_REQ
    """
    header_df = pd.read_csv(header_file_path)
    line_df = pd.read_csv(line_file_path)

    # ----------------------------------------------
    # Use schema intelligence as the primary mapper.
    # ----------------------------------------------
    header_mapping = get_intelligent_mapping(header_file_path)
    line_mapping = get_intelligent_mapping(line_file_path)

    header_order_field = header_mapping.get("order_id")
    description_field = header_mapping.get("customer_name")
    operation_field = header_mapping.get("operation_type")

    line_order_field = line_mapping.get("order_id")
    item_field = line_mapping.get("item")
    quantity_field = line_mapping.get("quantity")

    # ----------------------------------------------
    # Fallbacks for fields that intelligence missed.
    # ----------------------------------------------
    if not header_order_field:
        header_order_field = find_column(
            header_df.columns,
            [
                "ORD_ORDINE",
                "sales_order_id",
                "order_number",
                "client_order_ref",
                "po_num",
                "order_id",
            ],
        )

    if not description_field:
        description_field = find_column(
            header_df.columns,
            [
                "ORD_DES",
                "customer_name",
                "description",
                "company_name",
                "buyer",
            ],
        )

    if not operation_field:
        operation_field = find_column(
            header_df.columns,
            [
                "ORD_TIPOOP",
                "operation_type",
                "process_type",
                "fulfillment_mode",
                "order_type",
            ],
        )

    if not line_order_field:
        line_order_field = find_column(
            line_df.columns,
            [
                "RIG_ORDINE",
                "sales_order_id",
                "order_number",
                "client_order_ref",
                "po_ref",
                "order_id",
            ],
        )

    if not item_field:
        item_field = find_column(
            line_df.columns,
            [
                "RIG_ARTICOLO",
                "item",
                "sku",
                "item_code",
                "material_code",
                "part_no",
                "part_number",
                "product_sku",
                "product_code",
            ],
        )

    if not quantity_field:
        quantity_field = find_column(
            line_df.columns,
            [
                "RIG_QTAR",
                "quantity",
                "qty",
                "requested_quantity",
                "qty_requested",
                "ordered_qty",
            ],
        )

    # ----------------------------------------------
    # Required Field Validation
    # ----------------------------------------------
    if not header_order_field:
        raise ValueError(
            f"Could not detect header order field. Header columns: {list(header_df.columns)}"
        )

    if not line_order_field:
        raise ValueError(
            f"Could not detect line order field. Line columns: {list(line_df.columns)}"
        )

    if not item_field:
        raise ValueError(
            f"Could not detect item field. Line columns: {list(line_df.columns)}"
        )

    if not quantity_field:
        raise ValueError(
            f"Could not detect quantity field. Line columns: {list(line_df.columns)}"
        )

    # ----------------------------------------------
    # Build WMS Orders
    # ----------------------------------------------
    orders = []

    for _, header in header_df.iterrows():
        order_number = str(header[header_order_field])

        matching_lines = line_df[
            line_df[line_order_field].astype(str)
            == order_number
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

        # Normalize common operation descriptions.
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


# ==================================================
# Parse ERP Orders CSV
# ==================================================
def parse_erp_orders_csv(
    header_file_path: str,
    line_file_path: str | None = None,
):
    """
    Main order CSV parser.

    Supports:
    - Single flat CSV file
    - Separate header CSV + line CSV files
    """
    if line_file_path is None:
        return parse_single_file_orders_csv(
            header_file_path,
        )

    return parse_header_line_orders_csv(
        header_file_path,
        line_file_path,
    )


# ==================================================
# Parse Customer Orders CSV
# ==================================================
def parse_customer_orders_csv(
    header_file_path: str,
    line_file_path: str | None = None,
):
    """
    Compatibility wrapper used by existing tools.
    """
    return parse_erp_orders_csv(
        header_file_path,
        line_file_path,
    )


# ==================================================
# Manual Test
# ==================================================
if __name__ == "__main__":

    # Header/line test
    orders = parse_erp_orders_csv(
        "data/sample_files/test_ui_headers.csv",
        "data/sample_files/test_ui_lines.csv",
    )

    for order in orders:
        print(order)