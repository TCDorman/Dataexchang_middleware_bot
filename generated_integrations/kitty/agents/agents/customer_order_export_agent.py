"""
customer_order_export_agent.py

Exports processed/internal orders back into the customer's
original import format.

Important:
Only order/ordini imports are allowed to export back.
Item/articoli imports are skipped.
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Union


ORDER_TYPES = {
    "order",
    "orders",
    "ordini",
    "ordine",
    "sales_order",
    "customer_order",
}

ITEM_TYPES = {
    "item",
    "items",
    "articoli",
    "articolo",
    "article",
    "articles",
    "product",
    "products",
    "sku",
    "skus",
}


def get_safe_customer_name(customer_name: str) -> str:
    return customer_name.strip().lower().replace(" ", "_")


def find_customer_profile_path(customer_name: str) -> Path:
    safe_name = get_safe_customer_name(customer_name)

    possible_paths = [
        Path("configs/customers") / f"{safe_name}_profile.json",
        Path("configs/customers") / f"{safe_name}.json",
        Path("generated_integrations") / safe_name / "mapping_profile.json",
        Path("generated_integrations") / safe_name / "import_profile.json",
        Path("generated_integrations") / safe_name / "config.json",
    ]

    for path in possible_paths:
        if path.exists():
            return path

    raise FileNotFoundError(
        f"No saved customer profile found for '{customer_name}'. "
        f"Checked: {[str(path) for path in possible_paths]}"
    )


def load_json_file(path: Union[str, Path]) -> Union[Dict, List]:
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def extract_orders(internal_orders_data: Union[Dict, List]) -> List[Dict]:
    if isinstance(internal_orders_data, list):
        return internal_orders_data

    if isinstance(internal_orders_data, dict):
        return (
            internal_orders_data.get("orders")
            or internal_orders_data.get("ordini")
            or internal_orders_data.get("data")
            or internal_orders_data.get("result", {}).get("orders")
            or internal_orders_data.get("conversion", {}).get("orders")
            or internal_orders_data.get("export", {}).get("orders")
            or []
        )

    return []


def get_import_mapping(customer_profile: Dict) -> Dict:
    mapping = (
        customer_profile.get("field_mappings")
        or customer_profile.get("mappings")
        or customer_profile.get("mapping")
        or customer_profile.get("columns")
        or customer_profile.get("export_mapping")
        or {}
    )

    if not mapping:
        raise ValueError(
            "Customer profile is missing a mapping section. "
            "Expected one of: field_mappings, mappings, mapping, columns, export_mapping."
        )

    return mapping


def determine_document_type_from_profile(customer_profile: Dict) -> str:
    explicit_type = (
        customer_profile.get("document_type")
        or customer_profile.get("import_type")
        or customer_profile.get("file_type")
        or customer_profile.get("data_type")
        or customer_profile.get("source_document_type")
        or ""
    )

    explicit_type = str(explicit_type).strip().lower()

    if explicit_type:
        return explicit_type

    mapping = get_import_mapping(customer_profile)
    headers_found = customer_profile.get("headers_found", [])

    searchable_text = " ".join(
        list(mapping.keys())
        + list(mapping.values())
        + headers_found
    ).lower()

    order_keywords = [
        "order",
        "orders",
        "ordini",
        "ordine",
        "po_num",
        "po",
        "buyer",
        "customer",
        "cust",
        "qty_req",
        "quantity",
        "ship_to",
    ]

    item_keywords = [
        "item_master",
        "articoli",
        "articolo",
        "sku",
        "part_no",
        "part",
        "description",
        "descr",
        "uom",
        "unit",
        "weight",
        "length",
        "width",
        "height",
    ]

    order_score = sum(1 for keyword in order_keywords if keyword in searchable_text)
    item_score = sum(1 for keyword in item_keywords if keyword in searchable_text)

    if order_score >= item_score and order_score > 0:
        return "ordini"

    if item_score > order_score:
        return "articoli"

    return "unknown"


def is_order_document(document_type: str) -> bool:
    clean_type = str(document_type).strip().lower()
    return clean_type in ORDER_TYPES


def reverse_mapping(import_mapping: Dict) -> Dict:
    internal_fields = {
        "order_id",
        "customer_name",
        "item",
        "quantity",
    }

    mapping_keys = set(import_mapping.keys())

    if mapping_keys.intersection(internal_fields):
        return import_mapping

    return {
        internal_field: customer_field
        for customer_field, internal_field in import_mapping.items()
    }


def export_orders_to_customer_csv(
    orders: List[Dict],
    customer_profile: Dict,
    output_path: str,
) -> Dict:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    import_mapping = get_import_mapping(customer_profile)
    export_mapping = reverse_mapping(import_mapping)

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

            for internal_field, customer_field in export_mapping.items():
                customer_row[customer_field] = internal_row.get(
                    internal_field,
                    "",
                )

            rows.append(customer_row)

    if not rows:
        raise ValueError("No order rows available to export.")

    headers = list(rows[0].keys())

    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    return {
        "status": "success",
        "source_type": "csv",
        "document_type": "ordini",
        "orders_exported": len(orders),
        "rows_exported": len(rows),
        "output_path": str(output_file),
    }


def export_orders_back_to_customer_format(
    customer_profile_path: str,
    internal_orders_path: str,
    output_path: str,
) -> Dict:
    customer_profile = load_json_file(customer_profile_path)
    internal_orders_data = load_json_file(internal_orders_path)

    source_type = customer_profile.get("source_type", "csv").lower()
    document_type = determine_document_type_from_profile(customer_profile)

    if not is_order_document(document_type):
        return {
            "status": "skipped",
            "source_type": source_type,
            "document_type": document_type,
            "reason": (
                "Export skipped. Only ordini/order imports are exported "
                "back to the customer format. Articoli/item imports are not exported."
            ),
            "output_path": None,
        }

    orders = extract_orders(internal_orders_data)

    if not orders:
        raise ValueError("No orders found in internal orders file.")

    if source_type == "csv":
        return export_orders_to_customer_csv(
            orders=orders,
            customer_profile=customer_profile,
            output_path=output_path,
        )

    raise NotImplementedError(
        f"Export for source_type '{source_type}' is not implemented yet."
    )


def export_orders_for_customer(
    customer_name: str,
    internal_orders_path: str,
    output_path: str,
) -> Dict:
    customer_profile_path = find_customer_profile_path(customer_name)

    result = export_orders_back_to_customer_format(
        customer_profile_path=str(customer_profile_path),
        internal_orders_path=internal_orders_path,
        output_path=output_path,
    )

    result["customer_name"] = customer_name
    result["customer_profile_path"] = str(customer_profile_path)

    return result