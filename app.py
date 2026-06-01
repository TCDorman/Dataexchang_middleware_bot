from pathlib import Path
import tempfile
import json

import pandas as pd
import streamlit as st

from models.wms_models import WMSOrder, WMSOrderLine
from parsers.rest_api_parser import parse_api_orders
from transformers.wms_xml_transformer import export_orders_to_xml


st.set_page_config(
    page_title="Modula WMS Integration Agent",
    layout="wide",
)

st.title("Modula WMS Integration Agent")
st.write("Convert ERP CSV or REST API JSON data into Modula WMS XML.")

input_type = st.selectbox(
    "Choose input type",
    ["CSV Order Header + Line Files", "REST API JSON File"],
)

output_dir = Path("data/output")
output_dir.mkdir(parents=True, exist_ok=True)


def save_uploaded_file(uploaded_file, suffix):
    uploaded_file.seek(0)

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(uploaded_file.read())
        return temp_file.name


def find_column(columns, possible_names):
    for name in possible_names:
        if name in columns:
            return name
    return None


def parse_orders_from_csv(header_file_path, line_file_path):
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

        description = str(header[description_field]) if description_field else f"Order {order_number}"
        operation_type = str(header[operation_field]) if operation_field else "P"

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


if input_type == "CSV Order Header + Line Files":

    header_file = st.file_uploader("Upload order header CSV", type=["csv"])
    line_file = st.file_uploader("Upload order line CSV", type=["csv"])

    if st.button("Convert CSV to WMS XML"):

        if not header_file or not line_file:
            st.error("Please upload both header and line CSV files.")

        else:
            header_path = save_uploaded_file(header_file, ".csv")
            line_path = save_uploaded_file(line_file, ".csv")

            orders = parse_orders_from_csv(header_path, line_path)

            output_path = output_dir / "ui_csv_orders_wms.xml"

            export_orders_to_xml(orders, str(output_path))

            xml_content = output_path.read_text(encoding="utf-8")

            st.success(f"Converted {len(orders)} orders.")

            st.code(xml_content, language="xml")

            st.download_button(
                "Download WMS XML",
                data=xml_content,
                file_name="csv_orders_wms.xml",
                mime="application/xml",
            )


if input_type == "REST API JSON File":

    json_file = st.file_uploader("Upload REST API JSON response", type=["json"])

    if st.button("Convert JSON to WMS XML"):

        if not json_file:
            st.error("Please upload a JSON file.")

        else:
            api_data = json.load(json_file)

            orders = parse_api_orders(api_data)

            output_path = output_dir / "ui_api_orders_wms.xml"

            export_orders_to_xml(orders, str(output_path))

            xml_content = output_path.read_text(encoding="utf-8")

            st.success(f"Converted {len(orders)} orders.")

            st.code(xml_content, language="xml")

            st.download_button(
                "Download WMS XML",
                data=xml_content,
                file_name="api_orders_wms.xml",
                mime="application/xml",
            )