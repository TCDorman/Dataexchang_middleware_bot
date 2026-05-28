import sys
from pathlib import Path
import json
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models.wms_models import WMSOrder, WMSOrderLine
from transformers.wms_xml_transformer import export_orders_to_xml
from scripts.format_wms_xml import format_wms_xml


def load_mapping_config(config_path: str):
    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


def find_source_field_for_internal(mapping_config: dict, internal_field: str):
    for source_field, mapping in mapping_config.items():
        if mapping["internal_field"] == internal_field:
            return source_field

    return None


def row_to_internal_data(row, mapping_config: dict):
    data = {}

    for column in row.index:
        if column in mapping_config:
            internal_field = mapping_config[column]["internal_field"]
            data[internal_field] = row[column]

    return data


def convert_csv_with_mapping(
    header_file_path: str,
    line_file_path: str,
    mapping_config_path: str,
):
    header_df = pd.read_csv(header_file_path)
    line_df = pd.read_csv(line_file_path)

    mapping_config = load_mapping_config(mapping_config_path)

    line_order_source_field = find_source_field_for_internal(
        mapping_config,
        "order_number",
    )

    if not line_order_source_field:
        raise ValueError("No source field mapped to internal field: order_number")

    orders = []

    for _, header in header_df.iterrows():
        order_data = row_to_internal_data(header, mapping_config)

        order_number = str(order_data.get("order_number"))

        lines = []

        matching_lines = line_df[
            line_df[line_order_source_field].astype(str) == order_number
        ]

        for _, row in matching_lines.iterrows():
            line_data = row_to_internal_data(row, mapping_config)

            lines.append(
                WMSOrderLine(
                    order_number=order_number,
                    item_code=str(line_data.get("item_code")),
                    quantity=float(line_data.get("quantity", 0)),
                )
            )

        orders.append(
            WMSOrder(
                order_number=order_number,
                description=str(order_data.get("description", "")),
                operation_type=str(order_data.get("operation_type", "P")),
                lines=lines,
            )
        )

    output_path = "data/output/dynamic_mapped_orders.xml"

    export_orders_to_xml(orders, output_path)
    format_wms_xml(output_path)

    return output_path


if __name__ == "__main__":
    output = convert_csv_with_mapping(
        "data/sample_files/test_ui_headers.csv",
        "data/sample_files/test_ui_lines.csv",
        "configs/mappings/sample_mapping_config.json",
    )

    print(f"\nGenerated XML:\n{output}")