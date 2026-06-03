"""
csv_order_parser.py

CSV parser for customer order files.

This parser can work in two modes:

1. Standard mode:
   Uses expected internal headers like order_id, customer_name, item, quantity.

2. Profile mode:
   Uses a customer profile to map customer-specific headers into the
   internal Modula order format.
"""

import csv
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


class CsvOrderParser:
    """
    Parses CSV order files into the internal order dictionary format.
    """

    def parse(
        self,
        file_path: str,
        profile: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Parse a CSV file into internal order dictionaries.

        Args:
            file_path: Path to the CSV file.
            profile: Optional customer profile containing field mappings.

        Returns:
            List of orders grouped by order ID.
        """

        path = Path(file_path)
        grouped_orders = defaultdict(list)

        with path.open(mode="r", newline="", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)

            for row in reader:
                # If a profile is provided, map customer-specific headers
                # into the internal field names before processing.
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
        """
        Convert customer-specific CSV headers into internal field names.

        Args:
            row: Original CSV row.
            profile: Customer profile with field_mapping.

        Returns:
            Row using internal field names.
        """

        mapping = profile.get("field_mapping", {})
        mapped_row = {}

        for source_field, target_field in mapping.items():
            if source_field in row:
                mapped_row[target_field] = row[source_field]

        return mapped_row

    def _build_orders(
        self,
        grouped_orders: Dict[str, List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """
        Convert grouped CSV rows into internal order dictionaries.

        Args:
            grouped_orders: Rows grouped by order ID.

        Returns:
            List of internal order dictionaries.
        """

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