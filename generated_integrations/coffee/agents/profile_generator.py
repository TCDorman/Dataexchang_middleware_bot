import csv
import json
from pathlib import Path


# ==================================================
# Expected Modula Fields
# ==================================================
EXPECTED_FIELDS = [
    "order_id",
    "customer_name",
    "item",
    "quantity",
]


# ==================================================
# Header Aliases
# ==================================================
HEADER_ALIASES = {
    "order_id": [
        "order_id",
        "order",
        "order_number",
        "po",
        "po_num",
        "po_number",
        "purchase_order",
    ],
    "customer_name": [
        "customer_name",
        "customer",
        "buyer",
        "client",
        "account",
    ],
    "item": [
        "item",
        "item_number",
        "part",
        "part_no",
        "part_number",
        "sku",
        "material",
    ],
    "quantity": [
        "quantity",
        "qty",
        "qty_req",
        "qty_required",
        "amount",
        "count",
    ],
}


# ==================================================
# Normalize Header
# ==================================================
def normalize_header(header: str) -> str:
    return header.strip().lower().replace(" ", "_")


# ==================================================
# Read CSV Headers
# ==================================================
def read_csv_headers(file_path: str) -> list[str]:
    path = Path(file_path)

    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)
        return next(reader)


# ==================================================
# Suggest Mapping
# ==================================================
def suggest_mapping(headers: list[str]) -> dict:
    mapping = {}

    normalized_headers = {
        normalize_header(header): header
        for header in headers
    }

    for expected_field in EXPECTED_FIELDS:
        mapping[expected_field] = None

        aliases = HEADER_ALIASES.get(expected_field, [])

        for alias in aliases:
            normalized_alias = normalize_header(alias)

            if normalized_alias in normalized_headers:
                mapping[expected_field] = normalized_headers[normalized_alias]
                break

    return mapping


# ==================================================
# Generate Profile From CSV
# ==================================================
def generate_profile_from_csv(
    customer_name: str,
    file_path: str,
    source_type: str = "csv",
) -> dict:
    headers = read_csv_headers(file_path)
    mapping = suggest_mapping(headers)

    profile = {
        "customer_name": customer_name,
        "source_type": source_type,
        "mapping": mapping,
        "headers_found": headers,
    }

    return profile


# ==================================================
# Save Customer Profile
# ==================================================
def save_customer_profile(profile: dict) -> str:
    customer_name = profile["customer_name"]
    safe_name = customer_name.strip().lower().replace(" ", "_")

    output_folder = Path("configs/customers")
    output_folder.mkdir(parents=True, exist_ok=True)

    output_path = output_folder / f"{safe_name}_profile.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(profile, file, indent=4)

    return str(output_path)


# ==================================================
# Manual Test
# ==================================================
if __name__ == "__main__":
    profile = generate_profile_from_csv(
        customer_name="Ford",
        file_path="data/customer_input/test_headers.csv",
    )

    profile_path = save_customer_profile(profile)

    print(json.dumps(profile, indent=4))
    print(f"Profile saved to: {profile_path}")