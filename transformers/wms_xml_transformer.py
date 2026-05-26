import sys
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.append(str(Path(__file__).resolve().parents[1]))

from parsers.xml_parser import parse_items, parse_orders


def export_items_to_xml(items, output_path):
    root = ET.Element("MODULA_WMS")

    for item in items:
        item_node = ET.SubElement(root, "IMP_ARTICOLI")
        ET.SubElement(item_node, "ART_ARTICOLO").text = item.item_code
        ET.SubElement(item_node, "ART_DES").text = item.description or ""

    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


def export_orders_to_xml(orders, output_path):
    root = ET.Element("SYSTORE")

    for order in orders:
        order_node = ET.SubElement(root, "IMP_ORDINI")
        ET.SubElement(order_node, "ORD_ORDINE").text = order.order_number
        ET.SubElement(order_node, "ORD_DES").text = order.description or ""
        ET.SubElement(order_node, "ORD_TIPOOP").text = order.operation_type

        for line in order.lines:
            line_node = ET.SubElement(order_node, "IMP_ORDINI_RIGHE")
            ET.SubElement(line_node, "RIG_ORDINE").text = line.order_number
            ET.SubElement(line_node, "RIG_ARTICOLO").text = line.item_code
            ET.SubElement(line_node, "RIG_SUB1").text = line.sub1 or ""
            ET.SubElement(line_node, "RIG_SUB2").text = line.sub2 or ""
            ET.SubElement(line_node, "RIG_QTAR").text = str(line.quantity)

    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    Path("data/output").mkdir(parents=True, exist_ok=True)

    items = parse_items("data/sample_files/CFG-IMP-ARTICOLI.xml")
    orders = parse_orders("data/sample_files/CFG-IMP-ORDINI.xml")

    export_items_to_xml(items, "data/output/items_export.xml")
    export_orders_to_xml(orders, "data/output/orders_export.xml")

    print("Exported XML files to data/output/")