"""
csv_header_line_parser.py

Parses separate CSV header and line files into the internal order format.

Example:

headers.csv:
order_id,customer_name
ORD-1001,Ford

lines.csv:
order_id,item,quantity
ORD-1001,ABC123,5
ORD-1001,XYZ789,2

Output:
[
    {
        "order_id": "ORD-1001",
        "customer_name": "Ford",
        "lines": [
            {"item": "ABC123", "quantity": "5"},
            {"item": "XYZ789", "quantity": "2"}
        ]
    }
]
"""

import csv
from pathlib import Path
from typing import Any, Dict, List


class CsvHeaderLineParser:
    """
    Parses separate order header and line CSV files.
    """

    def parse(
        self,
        header_file_path: str,
        line_file_path: str,
    ) -> List[Dict[str, Any]]:
        """
        Parse header and line files into internal order dictionaries.

        Args:
            header_file_path: Path to order header CSV.
            line_file_path: Path to order line CSV.

        Returns:
            List of internal order dictionaries.
        """

        headers = self._read_csv(header_file_path)
        lines = self._read_csv(line_file_path)

        orders_by_id = {}

        for header_row in headers:
            order_id = (
                header_row.get("order_id")
                or header_row.get("OrderID")
                or header_row.get("Order ID")
            )

            if not order_id:
                continue

            orders_by_id[order_id] = {
                "order_id": order_id,
                "customer_name": (
                    header_row.get("customer_name")
                    or header_row.get("CustomerName")
                    or header_row.get("Customer Name")
                    or ""
                ),
                "lines": [],
            }

        for line_row in lines:
            order_id = (
                line_row.get("order_id")
                or line_row.get("OrderID")
                or line_row.get("Order ID")
            )

            if not order_id:
                continue

            if order_id not in orders_by_id:
                orders_by_id[order_id] = {
                    "order_id": order_id,
                    "customer_name": "",
                    "lines": [],
                }

            orders_by_id[order_id]["lines"].append(
                {
                    "item": (
                        line_row.get("item")
                        or line_row.get("Item")
                        or line_row.get("part_number")
                        or line_row.get("PartNumber")
                        or line_row.get("SKU")
                        or ""
                    ),
                    "quantity": (
                        line_row.get("quantity")
                        or line_row.get("Quantity")
                        or line_row.get("qty")
                        or line_row.get("Qty")
                        or ""
                    ),
                }
            )

        return list(orders_by_id.values())

    def _read_csv(
        self,
        file_path: str,
    ) -> List[Dict[str, Any]]:
        """
        Read a CSV file into dictionaries.

        Args:
            file_path: CSV file path.

        Returns:
            List of row dictionaries.
        """

        path = Path(file_path)

        with path.open(
            mode="r",
            newline="",
            encoding="utf-8-sig",
        ) as csv_file:
            reader = csv.DictReader(csv_file)
            return list(reader)