"""
sql_order_parser.py

Converts SQL query results into the internal order structure used by
the Modula XML exporter.
"""

import json
from collections import defaultdict
from pathlib import Path


class SqlOrderParser:
    def parse_rows_from_profile(
        self,
        rows: list[dict],
        profile_path: str,
    ) -> list[dict]:
        profile = self._load_profile(profile_path)
        field_mappings = profile.get("field_mappings", {})

        grouped_orders = defaultdict(list)

        order_id_mapping = field_mappings.get("order_id")
        if not order_id_mapping:
            raise ValueError("SQL profile is missing order_id mapping.")

        order_id_column = order_id_mapping.get("column_name")

        for row in rows:
            order_id = row.get(order_id_column)

            if order_id is None:
                continue

            grouped_orders[str(order_id)].append(row)

        orders = []

        for order_id, order_rows in grouped_orders.items():
            first_row = order_rows[0]

            order = {
                "order_id": order_id,
                "customer_name": self._get_mapped_value(
                    first_row,
                    field_mappings,
                    "customer_name",
                ),
                "ship_to_name": self._get_mapped_value(
                    first_row,
                    field_mappings,
                    "ship_to_name",
                ),
                "ship_to_address": self._get_mapped_value(
                    first_row,
                    field_mappings,
                    "ship_to_address",
                ),
                "lines": [],
            }

            for row in order_rows:
                line = {
                    "item": self._get_mapped_value(
                        row,
                        field_mappings,
                        "item",
                    ),
                    "quantity": self._get_mapped_value(
                        row,
                        field_mappings,
                        "quantity",
                    ),
                    "location": self._get_mapped_value(
                        row,
                        field_mappings,
                        "location",
                    ),
                }

                order["lines"].append(line)

            orders.append(order)

        return orders

    def _load_profile(self, profile_path: str) -> dict:
        path = Path(profile_path)

        if not path.exists():
            raise FileNotFoundError(f"SQL profile not found: {profile_path}")

        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    def _get_mapped_value(
        self,
        row: dict,
        field_mappings: dict,
        modula_field: str,
    ):
        mapping = field_mappings.get(modula_field)

        if not mapping:
            return None

        column_name = mapping.get("column_name")

        if not column_name:
            return None

        return row.get(column_name)