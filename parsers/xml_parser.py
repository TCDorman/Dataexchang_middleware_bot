from pathlib import Path
import xml.etree.ElementTree as ET
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models.wms_models import WMSItem, WMSOrder, WMSOrderLine


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


if __name__ == "__main__":
    items = parse_items("data/sample_files/CFG-IMP-ARTICOLI.xml")
    orders = parse_orders("data/sample_files/CFG-IMP-ORDINI.xml")

    print("\nITEMS")
    for item in items:
        print(item)

    print("\nORDERS")
    for order in orders:
        print(order)