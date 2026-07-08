"""
customer_profile_matcher_agent.py

Automatically identifies which customer profile matches an incoming file
and whether the file appears to be ordini/orders or articoli/items.
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Optional


ORDER_KEYWORDS = {
    "order",
    "orders",
    "ordini",
    "ordine",
    "po",
    "po_num",
    "purchase_order",
    "buyer",
    "customer",
    "cust",
    "qty",
    "qty_req",
    "quantity",
}

ITEM_KEYWORDS = {
    "item",
    "items",
    "articoli",
    "articolo",
    "sku",
    "part",
    "part_no",
    "item_code",
    "description",
    "descr",
    "uom",
    "unit",
    "weight",
    "height",
    "width",
    "length",
}


def normalize(value: str) -> str:
    return str(value).strip().lower()


def get_safe_customer_name(customer_name: str) -> str:
    return customer_name.strip().lower().replace(" ", "_")


def load_json_file(path: Path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def extract_csv_headers(file_path: Path) -> List[str]:
    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)
        headers = next(reader, [])

    return [header.strip() for header in headers if header.strip()]


def extract_json_fields(file_path: Path) -> List[str]:
    data = load_json_file(file_path)

    fields = set()

    def walk(value):
        if isinstance(value, dict):
            for key, nested_value in value.items():
                fields.add(str(key))
                walk(nested_value)

        elif isinstance(value, list):
            for item in value[:5]:
                walk(item)

    walk(data)

    return sorted(fields)


def extract_file_fields(file_path: str) -> List[str]:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        return extract_csv_headers(path)

    if suffix == ".json":
        return extract_json_fields(path)

    if suffix == ".xml":
        return []

    return []


def get_profile_fields(profile: Dict) -> List[str]:
    fields = set()

    mapping = (
        profile.get("field_mappings")
        or profile.get("mappings")
        or profile.get("mapping")
        or profile.get("columns")
        or {}
    )

    if isinstance(mapping, dict):
        for key, value in mapping.items():
            fields.add(str(key))
            fields.add(str(value))

    for header in profile.get("headers_found", []):
        fields.add(str(header))

    return sorted(fields)


def score_profile_match(file_fields: List[str], profile: Dict) -> Dict:
    normalized_file_fields = {normalize(field) for field in file_fields}
    normalized_profile_fields = {
        normalize(field)
        for field in get_profile_fields(profile)
    }

    matches = normalized_file_fields.intersection(normalized_profile_fields)

    if not normalized_file_fields:
        score = 0
    else:
        score = len(matches) / len(normalized_file_fields)

    return {
        "score": score,
        "matched_fields": sorted(matches),
        "file_fields": sorted(normalized_file_fields),
        "profile_fields": sorted(normalized_profile_fields),
    }


def load_customer_profiles(
    profiles_folder: str = "configs/customers",
) -> List[Dict]:
    folder = Path(profiles_folder)
    folder.mkdir(parents=True, exist_ok=True)

    profiles = []

    for profile_path in sorted(folder.glob("*.json")):
        try:
            profile = load_json_file(profile_path)
            profile["_profile_path"] = str(profile_path)
            profiles.append(profile)
        except Exception:
            continue

    return profiles


def detect_document_type_from_fields(fields: List[str]) -> str:
    searchable_text = " ".join(fields).lower()

    order_score = sum(
        1 for keyword in ORDER_KEYWORDS
        if keyword in searchable_text
    )

    item_score = sum(
        1 for keyword in ITEM_KEYWORDS
        if keyword in searchable_text
    )

    if order_score > item_score and order_score > 0:
        return "ordini"

    if item_score > order_score and item_score > 0:
        return "articoli"

    if order_score == item_score and order_score > 0:
        return "ordini"

    return "unknown"


def match_customer_profile(
    file_path: str,
    profiles_folder: str = "configs/customers",
    minimum_score: float = 0.35,
) -> Dict:
    file_fields = extract_file_fields(file_path)
    document_type = detect_document_type_from_fields(file_fields)

    profiles = load_customer_profiles(profiles_folder)

    best_match: Optional[Dict] = None
    best_score_data: Optional[Dict] = None

    for profile in profiles:
        score_data = score_profile_match(
            file_fields=file_fields,
            profile=profile,
        )

        if best_score_data is None or score_data["score"] > best_score_data["score"]:
            best_match = profile
            best_score_data = score_data

    if not best_match or not best_score_data:
        return {
            "status": "no_match",
            "file_path": file_path,
            "document_type": document_type,
            "reason": "No customer profiles were available.",
        }

    if best_score_data["score"] < minimum_score:
        return {
            "status": "low_confidence",
            "file_path": file_path,
            "document_type": document_type,
            "score": best_score_data["score"],
            "matched_fields": best_score_data["matched_fields"],
            "reason": "No customer profile matched with enough confidence.",
        }

    return {
        "status": "matched",
        "file_path": file_path,
        "customer_name": best_match.get("customer_name"),
        "safe_customer_name": get_safe_customer_name(
            best_match.get("customer_name", "")
        ),
        "customer_profile_path": best_match.get("_profile_path"),
        "document_type": document_type,
        "score": best_score_data["score"],
        "matched_fields": best_score_data["matched_fields"],
    }