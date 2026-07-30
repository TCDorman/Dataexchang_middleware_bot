"""
always_on_runtime.py

Local always-on middleware runtime.

Watches a customer input folder, detects new CSV files, confirms mappings
when needed, converts files to Modula WMS XML, and moves processed files
out of the input folder.

Mapping behavior:
1. If a saved customer profile exists, reuse it automatically.
2. If no profile exists, ask OpenAI for a mapping suggestion.
3. If OpenAI fails, fall back to simple header-based heuristics.
4. Ask the user to confirm the mapping once.
5. Save the confirmed mapping for future files.
"""

import csv
import json
import shutil
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.openai_mapping_agent import infer_mapping_with_openai


INPUT_FOLDER = Path("runtime/customer_input")
OUTPUT_FOLDER = Path("runtime/modula_output")
PROCESSED_FOLDER = Path("runtime/processed")
ERROR_FOLDER = Path("runtime/errors")
PROFILE_FOLDER = Path("runtime/profiles")

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
        "output_format": "modula_wms_xml",
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


def suggest_mapping_from_headers(
    headers: list[str],
    sample_rows: list[dict],
) -> dict:
    """
    Suggest mapping using OpenAI first.
    Falls back to heuristic matching if OpenAI is unavailable.
    """

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
        print(f"OpenAI mapping failed, using heuristic fallback: {error}")

        mapping = {}

        for field in CANONICAL_FIELDS:
            mapping[field] = None

        for header in headers:
            clean = header.lower().strip()

            if clean in [
                "order_id",
                "order",
                "order_number",
                "ord_ordine",
                "po_num",
                "po_number",
            ]:
                mapping["order_id"] = header

            elif clean in [
                "customer",
                "customer_name",
                "buyer",
                "client",
                "ord_des",
                "description",
                "order_description",
            ]:
                mapping["customer_name"] = header

            elif clean in [
                "item",
                "sku",
                "sku_code",
                "part",
                "part_no",
                "part_number",
                "rig_articolo",
                "article",
                "article_number",
            ]:
                mapping["item"] = header

            elif clean in [
                "quantity",
                "qty",
                "order_qty",
                "qty_req",
                "required_qty",
                "rig_qtar",
            ]:
                mapping["quantity"] = header

        return mapping


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

        prompt = (
            f"\nMap '{canonical_field}' "
            f"[suggested: {suggested or 'none'}]: "
        )

        user_value = input(prompt).strip()

        if user_value:
            confirmed_mapping[canonical_field] = user_value
        else:
            confirmed_mapping[canonical_field] = suggested

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
            f"Mapping confirmation failed. Invalid source columns: {invalid_columns}"
        )

    return confirmed_mapping


def add_text(parent: ET.Element, tag: str, value: str = "") -> ET.Element:
    element = ET.SubElement(parent, tag)
    element.text = str(value) if value is not None else ""
    return element


def convert_csv_to_modula_xml(
    file_path: Path,
    mapping: dict,
    output_path: Path,
) -> dict:
    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    orders_by_id = {}

    for row in rows:
        order_id = row.get(mapping["order_id"], "").strip()

        if not order_id:
            continue

        if order_id not in orders_by_id:
            customer_name = row.get(mapping["customer_name"], "").strip()

            orders_by_id[order_id] = {
                "order_id": order_id,
                "description": customer_name or order_id,
                "lines": [],
            }

        orders_by_id[order_id]["lines"].append(
            {
                "item": row.get(mapping["item"], "").strip(),
                "quantity": row.get(mapping["quantity"], "").strip(),
            }
        )

    root = ET.Element("SYSTORE")

    for order in orders_by_id.values():
        order_element = ET.SubElement(root, "IMP_ORDINI")

        add_text(order_element, "ORD_ORDINE", order["order_id"])
        add_text(order_element, "ORD_DES", order["description"])
        add_text(order_element, "ORD_TIPOOP", "P")

        for line in order["lines"]:
            line_element = ET.SubElement(order_element, "IMP_ORDINI_RIGHE")

            add_text(line_element, "RIG_ORDINE", order["order_id"])
            add_text(line_element, "RIG_ARTICOLO", line["item"])
            add_text(line_element, "RIG_SUB1")
            add_text(line_element, "RIG_SUB2")
            add_text(line_element, "RIG_STAMATE")
            add_text(line_element, "RIG_TIPOCONF")
            add_text(line_element, "RIG_HOSTINF")
            add_text(line_element, "RIG_QTAR", line["quantity"])
            add_text(line_element, "RIG_REQ_NOTE")
            add_text(line_element, "RIG_NOTE_STAMPA")
            add_text(line_element, "RIG_HOSTCAUS")
            add_text(line_element, "RIG_HOSTRIF")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ", level=0)
    tree.write(
        output_path,
        encoding="utf-8",
        xml_declaration=True,
    )

    return {
        "status": "success",
        "source_file": str(file_path),
        "orders_converted": len(orders_by_id),
        "rows_converted": len(rows),
        "output_path": str(output_path),
    }


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


def process_csv_file(file_path: Path, customer_name: str) -> dict:
    print(f"\nProcessing file: {file_path}")

    headers, preview_rows = read_csv_preview(file_path)

    if not headers:
        raise ValueError("CSV file has no headers.")

    profile = load_profile(customer_name)

    if profile:
        mapping = profile["field_mappings"]
        print(f"Loaded saved mapping profile for {customer_name}.")
    else:
        suggested_mapping = suggest_mapping_from_headers(
            headers=headers,
            sample_rows=preview_rows,
        )

        mapping = confirm_mapping(
            headers=headers,
            suggested_mapping=suggested_mapping,
        )

        profile_path = save_profile(customer_name, mapping)
        print(f"Saved mapping profile: {profile_path}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_FOLDER / f"{file_path.stem}_modula_{timestamp}.xml"

    result = convert_csv_to_modula_xml(
        file_path=file_path,
        mapping=mapping,
        output_path=output_path,
    )

    processed_path = move_file(file_path, PROCESSED_FOLDER)

    result["processed_path"] = str(processed_path)

    print("Conversion complete:")
    print(json.dumps(result, indent=4))

    return result


def scan_once(customer_name: str) -> None:
    ensure_runtime_folders()

    for file_path in sorted(INPUT_FOLDER.iterdir()):
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() != ".csv":
            continue

        try:
            process_csv_file(
                file_path=file_path,
                customer_name=customer_name,
            )

        except Exception as error:
            print(f"ERROR processing {file_path}: {error}")
            move_file(file_path, ERROR_FOLDER)


def run_forever(customer_name: str) -> None:
    ensure_runtime_folders()

    print("=" * 70)
    print("MODULA LOCAL MIDDLEWARE RUNTIME STARTED")
    print("=" * 70)
    print(f"Customer: {customer_name}")
    print(f"Watching: {INPUT_FOLDER}")
    print(f"Output: {OUTPUT_FOLDER}")
    print(f"Processed: {PROCESSED_FOLDER}")
    print(f"Errors: {ERROR_FOLDER}")
    print("=" * 70)

    while True:
        scan_once(customer_name)
        time.sleep(POLL_SECONDS)


def main():
    ensure_runtime_folders()

    print("Modula Local Middleware Runtime")
    print("=" * 70)

    customer_name = input("Enter customer name: ").strip()

    if not customer_name:
        raise ValueError("Customer name is required.")

    run_forever(customer_name)


if __name__ == "__main__":
    main()