import sys
from pathlib import Path
import json
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models.wms_models import WMSOrder, WMSOrderLine
from transformers.wms_xml_transformer import export_orders_to_xml
from scripts.format_wms_xml import format_wms_xml


def load_mapping_config(config_path):
    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


def find_field_by_internal(mapping_section, internal_field):
    for source_field, mapping in mapping_section.items():
        if mapping["internal_field"] == internal_field:
            return source_field
    return None


def convert_csv_with_mapping(header_file, line_file, mapping_config_file):

    header_df = pd.read_csv(header_file)
    line_df = pd.read_csv(line_file)

    config = load_mapping_config(mapping_config_file)

    header_mappings = config["header_mappings"]
    line_mappings = config["line_mappings"]

    # HEADER FIELD LOOKUPS
    header_order_field = find_field_by_internal(
        header_mappings,
        "order_number"
    )

    header_desc_field = find_field_by_internal(
        header_mappings,
        "description"
    )

    header_operation_field = find_field_by_internal(
        header_mappings,
        "operation_type"
    )

    # LINE FIELD LOOKUPS
    line_order_field = find_field_by_internal(
        line_mappings,
        "order_number"
    )

    line_item_field = find_field_by_internal(
        line_mappings,
        "item_code"
    )

    line_qty_field = find_field_by_internal(
        line_mappings,
        "quantity"
    )

    # VALIDATION
    if not header_order_field:
        raise ValueError(
            f"No header field mapped to order_number.\n"
            f"Header mappings:\n{header_mappings}"
        )

    if not line_order_field:
        raise ValueError(
            f"No line field mapped to order_number.\n"
            f"Line mappings:\n{line_mappings}"
        )

    if not line_item_field:
        raise ValueError(
            f"No line field mapped to item_code.\n"
            f"Line mappings:\n{line_mappings}"
        )

    if not line_qty_field:
        raise ValueError(
            f"No line field mapped to quantity.\n"
            f"Line mappings:\n{line_mappings}"
        )

    orders = []

    # PROCESS ORDERS
    for _, header in header_df.iterrows():

        order_number = str(header[header_order_field])

        matching_lines = line_df[
            line_df[line_order_field].astype(str) == order_number
        ]

        lines = []

        for _, row in matching_lines.iterrows():

            line = WMSOrderLine(
                order_number=order_number,
                item_code=str(row[line_item_field]),
                quantity=float(row[line_qty_field]),
            )

            lines.append(line)

        description = (
            str(header[header_desc_field])
            if header_desc_field
            else f"Order {order_number}"
        )

        operation_type = (
            str(header[header_operation_field])
            if header_operation_field
            else "P"
        )

        if operation_type.upper() == "PICK":
            operation_type = "P"

        order = WMSOrder(
            order_number=order_number,
            description=description,
            operation_type=operation_type,
            lines=lines,
        )

        orders.append(order)

    # OUTPUT
    output_path = "data/output/dynamic_mapped_orders.xml"

    export_orders_to_xml(orders, output_path)

    format_wms_xml(output_path)

    print(f"\nGenerated XML:\n{output_path}")

    return output_path


if __name__ == "__main__":

    convert_csv_with_mapping(
        "data/sample_files/test_ui_headers.csv",
        "data/sample_files/test_ui_lines.csv",
        "configs/mappings/csv_mapping_config.json",
    )