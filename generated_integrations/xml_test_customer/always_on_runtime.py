"""
always_on_runtime.py

Generated always-on local middleware runtime for XML Test Customer.
"""

import csv
import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from agents.openai_mapping_agent import infer_mapping_with_openai
except Exception:
    infer_mapping_with_openai = None


CUSTOMER_NAME = "XML Test Customer"

BASE_FOLDER = Path(__file__).resolve().parent
INPUT_FOLDER = BASE_FOLDER / "runtime" / "customer_input"
OUTPUT_FOLDER = BASE_FOLDER / "runtime" / "modula_output"
PROCESSED_FOLDER = BASE_FOLDER / "runtime" / "processed"
ERROR_FOLDER = BASE_FOLDER / "runtime" / "errors"
PROFILE_FOLDER = BASE_FOLDER / "runtime" / "profiles"

POLL_SECONDS = 5

CANONICAL_FIELDS = [
    "order_id",
    "customer_name",
    "item",
    "quantity",
]


def ensure_runtime_folders() -> None:
    for folder in [
        INPUT_FOLDER,
        OUTPUT_FOLDER,
        PROCESSED_FOLDER,
        ERROR_FOLDER,
        PROFILE_FOLDER,
    ]:
        folder.mkdir(parents=True, exist_ok=True)


def get_safe_customer_name(customer_name: str) -> str:
    return customer_name.strip().lower().replace(" ", "_")


def get_profile_path(customer_name: str) -> Path:
    safe_name = get_safe_customer_name(customer_name)
    return PROFILE_FOLDER / f"{safe_name}_profile.json"


def load_profile(customer_name: str) -> dict | None:
    profile_path = get_profile_path(customer_name)

    if not profile_path.exists():
        return None

    with open(profile_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_profile(customer_name: str, mapping: dict) -> Path:
    profile_path = get_profile_path(customer_name)

    profile = {
        "customer_name": customer_name,
        "source_type": "csv",
        "document_type": "ordini",
        "field_mappings": mapping,
        "created_at": datetime.now().isoformat(),
    }

    with open(profile_path, "w", encoding="utf-8") as file:
        json.dump(profile, file, indent=4)

    return profile_path


def read_csv_preview(file_path: Path) -> tuple[list[str], list[dict]]:
    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    return reader.fieldnames or [], rows[:5]


def heuristic_mapping(headers: list[str]) -> dict:
    mapping = {}

    for field in CANONICAL_FIELDS:
        mapping[field] = None

    for header in headers:
        clean = header.lower().strip()

        if clean in [
            "order_id",
            "order",
            "order_number",
            "po_num",
            "po_number",
        ]:
            mapping["order_id"] = header

        elif clean in [
            "customer",
            "customer_name",
            "buyer",
            "client",
        ]:
            mapping["customer_name"] = header

        elif clean in [
            "item",
            "sku",
            "sku_code",
            "part",
            "part_no",
            "part_number",
        ]:
            mapping["item"] = header

        elif clean in [
            "quantity",
            "qty",
            "order_qty",
            "qty_req",
            "required_qty",
        ]:
            mapping["quantity"] = header

    return mapping


def suggest_mapping(
    headers: list[str],
    sample_rows: list[dict],
) -> dict:
    if infer_mapping_with_openai is None:
        print("OpenAI mapping agent unavailable. Using heuristic fallback.")
        return heuristic_mapping(headers)

    try:
        print("\nAsking OpenAI to suggest field mappings...")

        ai_mapping = infer_mapping_with_openai(
            columns=headers,
            sample_rows=sample_rows,
        )

        mapping = {}

        for field in CANONICAL_FIELDS:
            mapping[field] = ai_mapping.get(field)

        print("OpenAI mapping suggestion received.")
        return mapping

    except Exception as error:
        print(f"OpenAI mapping failed. Using heuristic fallback: {error}")
        return heuristic_mapping(headers)


def confirm_mapping(headers: list[str], suggested_mapping: dict) -> dict:
    print("\nNew file structure detected.")
    print("=" * 70)
    print("Available columns:")

    for header in headers:
        print(f"- {header}")

    print("\nSuggested mapping:")
    print(json.dumps(suggested_mapping, indent=4))

    confirmed_mapping = {}

    for canonical_field in CANONICAL_FIELDS:
        suggested = suggested_mapping.get(canonical_field)

        user_value = input(
            f"\nMap '{canonical_field}' "
            f"[suggested: {suggested or 'none'}]: "
        ).strip()

        confirmed_mapping[canonical_field] = (
            user_value if user_value else suggested
        )

    missing = [
        field
        for field, source_column in confirmed_mapping.items()
        if not source_column
    ]

    if missing:
        raise ValueError(
            f"Mapping confirmation failed. Missing mappings: {missing}"
        )

    invalid_columns = [
        source_column
        for source_column in confirmed_mapping.values()
        if source_column not in headers
    ]

    if invalid_columns:
        raise ValueError(
            f"Mapping confirmation failed. Invalid columns: {invalid_columns}"
        )

    return confirmed_mapping


def convert_csv_to_modula_json(
    file_path: Path,
    mapping: dict,
    output_path: Path,
) -> dict:
    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    orders = []

    for row in rows:
        orders.append(
            {
                "order_id": row.get(mapping["order_id"], ""),
                "customer_name": row.get(mapping["customer_name"], ""),
                "lines": [
                    {
                        "item": row.get(mapping["item"], ""),
                        "quantity": row.get(mapping["quantity"], ""),
                    }
                ],
            }
        )

    result = {
        "status": "success",
        "customer_name": CUSTOMER_NAME,
        "source_file": str(file_path),
        "orders_converted": len(orders),
        "orders": orders,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=4)

    return result


def move_file(source_path: Path, target_folder: Path) -> Path:
    target_folder.mkdir(parents=True, exist_ok=True)

    target_path = target_folder / source_path.name

    if target_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_path = (
            target_folder
            / f"{source_path.stem}_{timestamp}{source_path.suffix}"
        )

    shutil.move(str(source_path), str(target_path))

    return target_path


def process_csv_file(file_path: Path) -> dict:
    print(f"\nProcessing file: {file_path}")

    headers, preview_rows = read_csv_preview(file_path)

    if not headers:
        raise ValueError("CSV file has no headers.")

    profile = load_profile(CUSTOMER_NAME)

    if profile:
        mapping = profile["field_mappings"]
        print(f"Loaded saved mapping profile for {CUSTOMER_NAME}.")
    else:
        suggested_mapping = suggest_mapping(
            headers=headers,
            sample_rows=preview_rows,
        )

        mapping = confirm_mapping(
            headers=headers,
            suggested_mapping=suggested_mapping,
        )

        profile_path = save_profile(CUSTOMER_NAME, mapping)
        print(f"Saved mapping profile: {profile_path}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_FOLDER / f"{file_path.stem}_modula_{timestamp}.json"

    result = convert_csv_to_modula_json(
        file_path=file_path,
        mapping=mapping,
        output_path=output_path,
    )

    processed_path = move_file(file_path, PROCESSED_FOLDER)

    result["output_path"] = str(output_path)
    result["processed_path"] = str(processed_path)

    print("Conversion complete:")
    print(json.dumps(result, indent=4))

    return result


def scan_once() -> None:
    ensure_runtime_folders()

    for file_path in sorted(INPUT_FOLDER.iterdir()):
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() != ".csv":
            continue

        try:
            process_csv_file(file_path)

        except Exception as error:
            print(f"ERROR processing {file_path}: {error}")
            move_file(file_path, ERROR_FOLDER)


def run_forever() -> None:
    ensure_runtime_folders()

    print("=" * 70)
    print("MODULA LOCAL MIDDLEWARE RUNTIME STARTED")
    print("=" * 70)
    print(f"Customer: {CUSTOMER_NAME}")
    print(f"Watching: {INPUT_FOLDER}")
    print(f"Output: {OUTPUT_FOLDER}")
    print(f"Processed: {PROCESSED_FOLDER}")
    print(f"Errors: {ERROR_FOLDER}")
    print("=" * 70)

    while True:
        scan_once()
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    run_forever()
