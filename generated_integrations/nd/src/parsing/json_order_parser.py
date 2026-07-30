"""
json_order_parser.py

Parses JSON order files into the internal order format.

Supported formats:

[
    {
        "order_id": "1001",
        "customer_name": "Ford",
        "item": "ABC123",
        "quantity": 5
    }
]

or

{
    "orders": [
        ...
    ]
}
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


class JsonOrderParser:
    """
    Parses JSON order files.
    """

    def parse(
        self,
        file_path: str,
        profile: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:

        path = Path(file_path)

        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, dict):
            records = data.get("orders", [])
        else:
            records = data

        grouped_orders = defaultdict(list)

        for row in records:

            if profile:
                row = self._map_row_with_profile(
                    row,
                    profile,
                )

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
                "customer_name": first_row.get(
                    "customer_name",
                    "",
                ),
                "lines": [],
            }

            for row in rows:

                order["lines"].append(
                    {
                        "item": row.get("item", ""),
                        "quantity": row.get(
                            "quantity",
                            "",
                        ),
                    }
                )

            orders.append(order)

        return orders