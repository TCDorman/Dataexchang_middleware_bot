import sys
from pathlib import Path
import json

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models.wms_models import WMSOrder, WMSOrderLine
from transformers.wms_xml_transformer import export_orders_to_xml
from scripts.format_wms_xml import format_wms_xml


def load_json_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_mapping_config(config_path):
    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


def find_mapping_by_internal(config, internal_field):
    for source_path, mapping in config.items():
        if mapping["internal_field"] == internal_field:
            return source_path
    return None


def get_nested_value(data, path):
    parts = path.split(".")
    current = data

    for part in parts:
        if isinstance(current, list):
            current = current[0] if current else None

        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None

    return current


def convert_json_with_mapping(input_json_file, mapping_config_file):
    data = load_json_file(input_json_file)
    config = load_mapping_config(mapping_config_file)

    orders_path = "orders"
    orders_data = data.get(orders_path, [])

    order_number_path = find_mapping_by_internal(config, "order_number")
    description_path = find_mapping_by_internal(config, "description")
    operation_type_path = find_mapping_by_internal(config, "operation_type")
    item_code_path = find_mapping_by_internal(config, "item_code")
    quantity_path = find_mapping_by_internal(config, "quantity")

    orders = []

    for order_data in orders_data:
        order_number = get_nested_value(
            {"orders": order_data},
            order_number_path,
        )

        description = get_nested_value(
            {"orders": order_data},
            description_path,
        )

        operation_type = get_nested_value(
            {"orders": order_data},
            operation_type_path,
        ) or "P"

        line_items = order_data.get("lines", [])

        lines = []

        for line_data in line_items:
            item_code = get_nested_value(
                {"orders": {"lines": line_data}},
                item_code_path,
            )

            quantity = get_nested_value(
                {"orders": {"lines": line_data}},
                quantity_path,
            )

            lines.append(
                WMSOrderLine(
                    order_number=str(order_number),
                    item_code=str(item_code),
                    quantity=float(quantity),
                )
            )

        orders.append(
            WMSOrder(
                order_number=str(order_number),
                description=str(description),
                operation_type=str(operation_type),
                lines=lines,
            )
        )

    output_path = "data/output/dynamic_json_orders.xml"

    export_orders_to_xml(orders, output_path)
    format_wms_xml(output_path)

    print(f"Generated XML: {output_path}")


if __name__ == "__main__":
    convert_json_with_mapping(
        "data/sample_files/sample_rest_api_order_response.json",
        "configs/mappings/json_mapping_config.json",
    )