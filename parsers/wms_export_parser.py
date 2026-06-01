import sys
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models.wms_models import WMSOrder, WMSOrderLine


def clean_text(value):
    return value.strip() if value else None


def parse_wms_order_export(file_path: str):
    tree = ET.parse(file_path)
    root = tree.getroot()

    orders = []

    for order_node in root.findall("EXP_ORDINI"):
        order_number = clean_text(order_node.findtext("ORD_ORDINE"))
        operation_type = clean_text(order_node.findtext("ORD_TIPOOP")) or "P"

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
            order_number=order_number,
            description=f"WMS Export Order {order_number}",
            operation_type=operation_type,
            warehouse_number=clean_text(order_node.findtext("ORD_ATTR1")),
            bay_number=clean_text(order_node.findtext("ORD_ELEBAIE")),
            lines=lines,
        )

        orders.append(order)

    return orders


if __name__ == "__main__":
    orders = parse_wms_order_export(
        "data/sample_files/CFG-EXP-ORDINI.xml"
    )

    print("\nWMS EXPORT ORDERS")

    for order in orders:
        print(order)