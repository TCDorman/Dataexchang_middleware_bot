"""
xml_order_parser.py

Parses XML order files into the internal order format.
"""

import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


class XmlOrderParser:
    """
    Parses simple XML order files.
    """

    def parse(
        self,
        file_path: str,
        profile: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        path = Path(file_path)
        tree = ET.parse(path)
        root = tree.getroot()

        records = []

        for element in root.iter():
            child_fields = {}

            for child in list(element):
                if child.text:
                    child_fields[child.tag] = child.text.strip()

            if child_fields:
                records.append(child_fields)

        grouped_orders = defaultdict(list)

        for row in records:
            if profile:
                row = self._map_row_with_profile(row, profile)

            order_id = row.get("order_id")

            if not order_id:
                continue

            grouped_orders[order_id].append(row)

        return self._build_orders(grouped_orders)

    def _map_row_with_profile(
        self,
        row: Dict[str, Any],
        profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        mapping = profile.get("field_mapping", {})
        mapped_row = {}

        for internal_field, source_field in mapping.items():
            if source_field in row:
                mapped_row[internal_field] = row[source_field]

        return mapped_row

    def _build_orders(
        self,
        grouped_orders,
    ) -> List[Dict[str, Any]]:
        orders = []

        for order_id, rows in grouped_orders.items():
            first_row = rows[0]

            order = {
                "order_id": order_id,
                "customer_name": first_row.get("customer_name", ""),
                "lines": [],
            }

            for row in rows:
                order["lines"].append(
                    {
                        "item": row.get("item", ""),
                        "quantity": row.get("quantity", ""),
                    }
                )

            orders.append(order)

        return orders