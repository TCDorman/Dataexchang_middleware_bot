import csv
from pathlib import Path


class CsvOrderParser:
    """
    Converts a customer CSV file into canonical order dicts
    using an AI-inferred field mapping.

    Field mapping format (from OpenAI mapping agent):
    {
        "order_id":       "Purchase Order",
        "customer_name":  "Company",
        "item":           "Part Number",
        "quantity":       "Requested Qty",
        "location":       null,
        ...
    }
    """

    def _get_val(self, row: dict, mapping: dict, canonical_key: str) -> str:
        source_col = mapping.get(canonical_key)
        if not source_col:
            return ""
        return str(row.get(source_col, "")).strip()

    def convert(self, file_path: str | Path, field_mapping: dict) -> list[dict]:
        file_path = Path(file_path)

        with open(file_path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            return []

        # Group rows by order_id
        orders: dict[str, dict] = {}

        for row in rows:
            order_id = self._get_val(row, field_mapping, "order_id")
            customer_name = self._get_val(row, field_mapping, "customer_name")
            item = self._get_val(row, field_mapping, "item")
            quantity = self._get_val(row, field_mapping, "quantity")

            if not order_id:
                continue  # skip rows with no order id

            if order_id not in orders:
                orders[order_id] = {
                    "order_id": order_id,
                    "customer_name": customer_name,
                    "lines": [],
                }

            if item:
                orders[order_id]["lines"].append({
                    "item": item,
                    "quantity": quantity,
                })

        return list(orders.values())