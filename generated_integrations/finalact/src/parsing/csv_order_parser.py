"""
csv_order_parser.py

CSV parser for customer order files.

Supports:
1. Standard internal headers
2. AI-generated profiles where field_mapping maps:
   internal_field -> source_header
3. Legacy profiles where field_mapping maps:
   source_header -> internal_field
"""

import csv
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


class CsvOrderParser:
    """
    Parses CSV order files into the internal order dictionary format.
    """

    INTERNAL_FIELDS = {
        "order_id",
        "customer_name",
        "item",
        "quantity",
    }

    def parse(
        self,
        file_path: str,
        profile: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        path = Path(file_path)
        grouped_orders = defaultdict(list)

        with path.open(mode="r", newline="", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)

            for row in reader:
                if profile:
                    row = self._map_row_with_profile(row, profile)

                order_id = (
                    row.get("order_id")
                    or row.get("OrderID")
                    or row.get("Order ID")
                )

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

        if not mapping:
            return row

        mapped_row = {}

        # AI format:
        # {
        #   "order_id": "PO_ID",
        #   "customer_name": "Buyer",
        #   "item": "PartNumber",
        #   "quantity": "AmountRequested"
        # }
        if self._is_internal_to_source_mapping(mapping):
            for internal_field, source_field in mapping.items():
                if source_field in row:
                    mapped_row[internal_field] = row[source_field]

        # Legacy format:
        # {
        #   "PO_ID": "order_id",
        #   "Buyer": "customer_name"
        # }
        else:
            for source_field, internal_field in mapping.items():
                if source_field in row:
                    mapped_row[internal_field] = row[source_field]

        return mapped_row

    def _is_internal_to_source_mapping(
        self,
        mapping: Dict[str, str],
    ) -> bool:
        return any(
            field in self.INTERNAL_FIELDS
            for field in mapping.keys()
        )

    def _build_orders(
        self,
        grouped_orders: Dict[str, List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        orders = []

        for order_id, rows in grouped_orders.items():
            first_row = rows[0]

            order = {
                "order_id": order_id,
                "customer_name": (
                    first_row.get("customer_name")
                    or first_row.get("CustomerName")
                    or first_row.get("Customer Name")
                    or ""
                ),
                "lines": [],
            }

            for row in rows:
                line = {
                    "item": (
                        row.get("item")
                        or row.get("Item")
                        or row.get("part_number")
                        or row.get("PartNumber")
                        or row.get("SKU")
                        or ""
                    ),
                    "quantity": (
                        row.get("quantity")
                        or row.get("Quantity")
                        or row.get("qty")
                        or row.get("Qty")
                        or ""
                    ),
                }

                order["lines"].append(line)

            orders.append(order)

        return orders