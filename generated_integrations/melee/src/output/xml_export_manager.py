"""
xml_export_manager.py

XML export manager for the Modula WMS Data Integration Agent.

This module is responsible for saving validated, transformed orders
as XML output files.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import xml.etree.ElementTree as ET


class XmlExportManager:
    """
    Exports transformed order data to XML files.
    """

    def __init__(self, output_dir: str = "data/output"):
        """
        Initialize the XML export manager.

        Args:
            output_dir: Folder where XML output files should be saved.
        """

        self.output_dir = Path(output_dir)

        # Ensure the output folder exists before trying to save files.
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_orders(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Export transformed orders to an XML file.

        Args:
            orders: List of transformed order dictionaries.

        Returns:
            Dictionary containing export status and output file path.
        """

        # Create a timestamped filename so exports do not overwrite each other.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"modula_orders_{timestamp}.xml"

        # Build the XML document structure.
        root = ET.Element("Orders")

        for order in orders:
            order_element = ET.SubElement(root, "Order")

            order_id = order.get("order_id") or order.get("OrderID") or ""
            customer_name = (
                order.get("customer_name")
                or order.get("CustomerName")
                or ""
            )

            ET.SubElement(order_element, "OrderID").text = str(order_id)
            ET.SubElement(order_element, "CustomerName").text = str(customer_name)

            lines_element = ET.SubElement(order_element, "Lines")
            lines = order.get("lines") or order.get("Lines") or []

            for line in lines:
                line_element = ET.SubElement(lines_element, "Line")

                item = (
                    line.get("item")
                    or line.get("Item")
                    or line.get("part_number")
                    or line.get("PartNumber")
                    or ""
                )

                quantity = (
                    line.get("quantity")
                    or line.get("Quantity")
                    or line.get("qty")
                    or ""
                )

                ET.SubElement(line_element, "Item").text = str(item)
                ET.SubElement(line_element, "Quantity").text = str(quantity)

        # Create the XML tree.
        tree = ET.ElementTree(root)

        # Pretty-print the XML for easier debugging and manual review.
        ET.indent(tree, space="    ", level=0)

        # Save the XML document to disk.
        tree.write(
            output_path,
            encoding="utf-8",
            xml_declaration=True,
        )

        return {
            "status": "success",
            "output_path": str(output_path),
            "orders_exported": len(orders),
        }