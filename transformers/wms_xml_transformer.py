import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models.wms_models import WMSItem, WMSOrder


def save_pretty_xml(root, output_path):
    rough_xml = ET.tostring(root, encoding="utf-8")
    parsed_xml = minidom.parseString(rough_xml)
    pretty_xml = parsed_xml.toprettyxml(indent="    ")

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(pretty_xml)


def export_items_to_xml(items: list[WMSItem], output_path: str):
    root = ET.Element("MODULA_WMS")

    for item in items:
        item_node = ET.SubElement(root, "IMP_ARTICOLI")
        ET.SubElement(item_node, "ART_ARTICOLO").text = item.item_code
        ET.SubElement(item_node, "ART_DES").text = item.description or ""

    save_pretty_xml(root, output_path)


def export_orders_to_xml(orders: list[WMSOrder], output_path: str):
    root = ET.Element("SYSTORE")

    for order in orders:
        order_node = ET.SubElement(root, "IMP_ORDINI")
        ET.SubElement(order_node, "ORD_ORDINE").text = order.order_number
        ET.SubElement(order_node, "ORD_DES").text = order.description or ""
        ET.SubElement(order_node, "ORD_TIPOOP").text = order.operation_type or "P"

        for line in order.lines:
            line_node = ET.SubElement(order_node, "IMP_ORDINI_RIGHE")
            ET.SubElement(line_node, "RIG_ORDINE").text = line.order_number
            ET.SubElement(line_node, "RIG_ARTICOLO").text = line.item_code
            ET.SubElement(line_node, "RIG_SUB1").text = line.sub1 or ""
            ET.SubElement(line_node, "RIG_SUB2").text = line.sub2 or ""
            ET.SubElement(line_node, "RIG_STAMATE").text = ""
            ET.SubElement(line_node, "RIG_TIPOCONF").text = ""
            ET.SubElement(line_node, "RIG_HOSTINF").text = ""
            ET.SubElement(line_node, "RIG_QTAR").text = str(line.quantity)
            ET.SubElement(line_node, "RIG_REQ_NOTE").text = ""
            ET.SubElement(line_node, "RIG_NOTE_STAMPA").text = ""
            ET.SubElement(line_node, "RIG_HOSTCAUS").text = ""
            ET.SubElement(line_node, "RIG_HOSTRIF").text = ""

    save_pretty_xml(root, output_path)