"""
customer_csv_exporter.py
"""

import csv
from pathlib import Path
from typing import Dict, List


class CustomerCsvExporter:
    def __init__(self, customer_profile: Dict):
        self.customer_profile = customer_profile

        self.import_mapping = (
            customer_profile.get("field_mappings")
            or customer_profile.get("mappings")
            or customer_profile.get("mapping")
            or customer_profile.get("columns")
            or {}
        )

        if not self.import_mapping:
            raise ValueError(
                "Customer profile is missing a mapping section. "
                "Expected one of: field_mappings, mappings, mapping, columns."
            )

        self.export_mapping = self._reverse_mapping(self.import_mapping)

    def _reverse_mapping(self, import_mapping: Dict) -> Dict:
        return {
            internal_field: customer_field
            for customer_field, internal_field in import_mapping.items()
        }

    def export_orders(
        self,
        orders: List[Dict],
        output_path: str,
    ) -> Dict:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        rows = []

        for order in orders:
            lines = order.get("lines", [])

            if not lines:
                lines = [{}]

            for line in lines:
                internal_row = {
                    "order_id": order.get("order_id", ""),
                    "customer_name": order.get("customer_name", ""),
                    "item": line.get("item", ""),
                    "quantity": line.get("quantity", ""),
                }

                customer_row = {}

                for internal_field, customer_field in self.export_mapping.items():
                    customer_row[customer_field] = internal_row.get(
                        internal_field,
                        "",
                    )

                rows.append(customer_row)

        if not rows:
            raise ValueError("No order rows available to export.")

        customer_headers = list(rows[0].keys())

        with open(output_file, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=customer_headers)
            writer.writeheader()
            writer.writerows(rows)

        return {
            "status": "success",
            "source_type": "csv",
            "orders_exported": len(orders),
            "rows_exported": len(rows),
            "output_path": str(output_file),
        }


# Compatibility alias in case older code expects this name
customer_csv_exporter = CustomerCsvExporter