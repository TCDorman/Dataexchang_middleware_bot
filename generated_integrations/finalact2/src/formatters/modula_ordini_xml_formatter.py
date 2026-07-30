import xml.etree.ElementTree as ET
from pathlib import Path


class ModulaOrdiniXmlFormatter:
    """
    Converts canonical order dicts into Modula WMS IMP_ORDINI XML.

    Expected canonical order structure:
    {
        "order_id": "ORDER11",
        "customer_name": "Some Name",   # optional, falls back to order_id
        "lines": [
            {"item": "ITEM01", "quantity": "2"},
            {"item": "ITEM02", "quantity": "2"},
        ]
    }
    """

    def _add(self, parent: ET.Element, tag: str, value: str = "") -> ET.Element:
        el = ET.SubElement(parent, tag)
        el.text = str(value) if value not in (None, "") else None
        return el

    def format_orders_to_xml(
        self,
        orders: list[dict],
        output_path: str | Path,
    ) -> dict:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        root = ET.Element("SYSTORE")

        for order in orders:
            order_id = str(order.get("order_id", "")).strip()
            customer_name = str(order.get("customer_name", "")).strip()
            description = customer_name if customer_name else order_id

            imp = ET.SubElement(root, "IMP_ORDINI")
            self._add(imp, "ORD_ORDINE", order_id)
            self._add(imp, "ORD_DES", description)
            self._add(imp, "ORD_TIPOOP", "P")

            for line in order.get("lines", []):
                rig = ET.SubElement(imp, "IMP_ORDINI_RIGHE")
                self._add(rig, "RIG_ORDINE", order_id)
                self._add(rig, "RIG_ARTICOLO", line.get("item", ""))
                self._add(rig, "RIG_SUB1")
                self._add(rig, "RIG_SUB2")
                self._add(rig, "RIG_STAMATE")
                self._add(rig, "RIG_TIPOCONF")
                self._add(rig, "RIG_HOSTINF")
                self._add(rig, "RIG_QTAR", line.get("quantity", ""))
                self._add(rig, "RIG_REQ_NOTE")
                self._add(rig, "RIG_NOTE_STAMPA")
                self._add(rig, "RIG_HOSTCAUS")
                self._add(rig, "RIG_HOSTRIF")

        ET.indent(root, space="    ")
        tree = ET.ElementTree(root)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)

        return {
            "status": "success",
            "orders_formatted": len(orders),
            "output_path": str(output_path),
        }