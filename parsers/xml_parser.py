import sys
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models.wms_models import WMSItem, WMSOrder, WMSOrderLine
from validators.wms_validator import validate_items, validate_orders


def parse_xml_file(file_path: str):
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    tree = ET.parse(path)
    return tree.getroot()


def clean_text(value):
    return value.strip() if value else None


def parse_items(file_path: str):
    root = parse_xml_file(file_path)
    items = []

    for item_node in root.findall("IMP_ARTICOLI"):
        item = WMSItem(
            item_code=clean_text(item_node.findtext("ART_ARTICOLO")),
            description=clean_text(item_node.findtext("ART_DES")),
        )
        items.append(item)

    return items


def parse_orders(file_path: str):
    root = parse_xml_file(file_path)
    orders = []

    for order_node in root.findall("IMP_ORDINI"):
        order_number = clean_text(order_node.findtext("ORD_ORDINE"))
        lines = []

        for line_node in order_node.findall("IMP_ORDINI_RIGHE"):
            line = WMSOrderLine(
                order_number=clean_text(line_node.findtext("RIG_ORDINE")),
                item_code=clean_text(line_node.findtext("RIG_ARTICOLO")),
                quantity=float(clean_text(line_node.findtext("RIG_QTAR")) or 0),
                sub1=clean_text(line_node.findtext("RIG_SUB1")),
                sub2=clean_text(line_node.findtext("RIG_SUB2")),
            )
            lines.append(line)

        order = WMSOrder(
            order_number=order_number,
            description=clean_text(order_node.findtext("ORD_DES")),
            operation_type=clean_text(order_node.findtext("ORD_TIPOOP")),
            lines=lines,
        )
        orders.append(order)

    return orders


def parse_export_orders(file_path: str):
    root = parse_xml_file(file_path)
    orders = []

    for order_node in root.findall("EXP_ORDINI"):
        lines = []

        for line_node in order_node.findall("EXP_ORDINI_RIGHE"):
            line = WMSOrderLine(
                order_number=clean_text(line_node.findtext("RIG_ORDINE")),
                item_code=clean_text(line_node.findtext("RIG_ARTICOLO")),
                quantity=float(clean_text(line_node.findtext("RIG_QTAE")) or 0),
                sub1=clean_text(line_node.findtext("RIG_SUB1")),
                warehouse_task=clean_text(line_node.findtext("RIG_ATTR1")),
                source_bin=clean_text(line_node.findtext("RIG_ATTR2")),
                destination_bin=clean_text(line_node.findtext("RIG_ATTR3")),
            )
            lines.append(line)

        order = WMSOrder(
            order_number=clean_text(order_node.findtext("ORD_ORDINE")),
            operation_type=clean_text(order_node.findtext("ORD_TIPOOP")),
            warehouse_number=clean_text(order_node.findtext("ORD_ATTR1")),
            bay_number=clean_text(order_node.findtext("ORD_ELEBAIE")),
            lines=lines,
        )
        orders.append(order)

    return orders


if __name__ == "__main__":
    items = parse_items("data/sample_files/CFG-IMP-ARTICOLI.xml")
    import_orders = parse_orders("data/sample_files/CFG-IMP-ORDINI.xml")
    export_orders = parse_export_orders("data/sample_files/CFG-EXP-ORDINI.xml")

    item_errors = validate_items(items)
    order_errors = validate_orders(import_orders)

    print("\nITEMS")
    for item in items:
        print(item)

    print("\nITEM VALIDATION")
    print(item_errors if item_errors else "No item validation errors")

    print("\nIMPORT ORDERS")
    for order in import_orders:
        print(order)

    print("\nEXPORT ORDERS")
    for order in export_orders:
        print(order)

    print("\nORDER VALIDATION")
    print(order_errors if order_errors else "No order validation errors")