import sys
from pathlib import Path
import json
import xml.etree.ElementTree as ET

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models.wms_models import WMSOrder, WMSOrderLine
from transformers.wms_xml_transformer import export_orders_to_xml
from scripts.format_wms_xml import format_wms_xml


def load_mapping_config(config_path):
    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


def find_path_by_internal(config, internal_field):
    for source_path, mapping in config.items():
        if mapping["internal_field"] == internal_field:
            return source_path
    return None


def strip_root_path(path):
    parts = path.split(".")
    return ".".join(parts[1:])


def get_child_text(parent, relative_path):
    current = parent

    for part in relative_path.split("."):
        current = current.find(part)

        if current is None:
            return None

    return current.text.strip() if current.text else None


def convert_xml_with_mapping(input_xml_file, mapping_config_file):
    config = load_mapping_config(mapping_config_file)

    tree = ET.parse(input_xml_file)
    root = tree.getroot()

    order_number_path = strip_root_path(
        find_path_by_internal(config, "order_number")
    )

    description_path = strip_root_path(
        find_path_by_internal(config, "description")
    )

    operation_type_path = strip_root_path(
        find_path_by_internal(config, "operation_type")
    )

    item_code_path = strip_root_path(
        find_path_by_internal(config, "item_code")
    )

    quantity_path = strip_root_path(
        find_path_by_internal(config, "quantity")
    )

    orders = []

    for order_node in root.findall("IMP_ORDINI"):
        order_number = get_child_text(order_node, "ORD_ORDINE")
        description = get_child_text(order_node, "ORD_DES")
        operation_type = get_child_text(order_node, "ORD_TIPOOP") or "P"

        lines = []

        for line_node in order_node.findall("IMP_ORDINI_RIGHE"):
            item_code = get_child_text(line_node, "RIG_ARTICOLO")
            quantity = get_child_text(line_node, "RIG_QTAR")

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

    output_path = "data/output/dynamic_xml_orders.xml"

    export_orders_to_xml(orders, output_path)
    format_wms_xml(output_path)

    print(f"Generated XML: {output_path}")


if __name__ == "__main__":
    convert_xml_with_mapping(
        "data/sample_files/CFG-IMP-ORDINI.xml",
        "configs/mappings/xml_mapping_config.json",
    )