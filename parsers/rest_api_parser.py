import sys
from pathlib import Path
import requests

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models.wms_models import WMSOrder, WMSOrderLine


def fetch_json_from_api(url: str, headers: dict | None = None):
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def parse_api_orders(api_data: dict):
    orders = []

    for order_data in api_data["orders"]:
        lines = []

        for line_data in order_data["lines"]:
            lines.append(
                WMSOrderLine(
                    order_number=order_data["order_id"],
                    item_code=line_data["sku"],
                    quantity=float(line_data["quantity"]),
                )
            )

        orders.append(
            WMSOrder(
                order_number=order_data["order_id"],
                description=order_data.get("description"),
                operation_type=order_data.get("operation_type", "P"),
                lines=lines,
            )
        )

    return orders


if __name__ == "__main__":
    sample_api_response = {
        "orders": [
            {
                "order_id": "API-1001",
                "description": "API Order 1001",
                "operation_type": "P",
                "lines": [
                    {"sku": "ITEM-API-01", "quantity": 3},
                    {"sku": "ITEM-API-02", "quantity": 5}
                ]
            },
            {
                "order_id": "API-1002",
                "description": "API Order 1002",
                "operation_type": "P",
                "lines": [
                    {"sku": "ITEM-API-03", "quantity": 2}
                ]
            }
        ]
    }

    orders = parse_api_orders(sample_api_response)

    print("\nREST API ORDERS")
    for order in orders:
        print(order)