import sys
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.append(str(Path(__file__).resolve().parents[1]))


def validate_wms_xml_file(file_path: str):
    path = Path(file_path)

    if not path.exists():
        return {
            "status": "error",
            "errors": [f"File not found: {file_path}"],
        }

    errors = []

    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except ET.ParseError as error:
        return {
            "status": "error",
            "errors": [f"Invalid XML: {error}"],
        }

    if root.tag not in ["SYSTORE", "MODULA_WMS"]:
        errors.append(
            f"Invalid root tag: {root.tag}. Expected SYSTORE or MODULA_WMS."
        )

    orders = root.findall("IMP_ORDINI")

    for order_index, order in enumerate(orders, start=1):
        order_number = order.findtext("ORD_ORDINE")
        operation_type = order.findtext("ORD_TIPOOP")

        if not order_number:
            errors.append(f"Order {order_index}: missing ORD_ORDINE")

        if not operation_type:
            errors.append(f"Order {order_index}: missing ORD_TIPOOP")

        lines = order.findall("IMP_ORDINI_RIGHE")

        if not lines:
            errors.append(f"Order {order_number}: has no line items")

        for line_index, line in enumerate(lines, start=1):
            item_code = line.findtext("RIG_ARTICOLO")
            quantity = line.findtext("RIG_QTAR")

            if not item_code:
                errors.append(
                    f"Order {order_number}, line {line_index}: missing RIG_ARTICOLO"
                )

            if not quantity:
                errors.append(
                    f"Order {order_number}, line {line_index}: missing RIG_QTAR"
                )

            try:
                if quantity is not None and float(quantity) <= 0:
                    errors.append(
                        f"Order {order_number}, line {line_index}: quantity must be greater than 0"
                    )
            except ValueError:
                errors.append(
                    f"Order {order_number}, line {line_index}: invalid quantity value {quantity}"
                )

    return {
        "status": "success" if not errors else "error",
        "errors": errors,
    }