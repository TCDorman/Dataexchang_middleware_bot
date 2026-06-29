"""
always_on_runtime.py

Generated always-on AI middleware runtime for Quick Test Customer.

This runtime is designed to act as a local AI middleware agent.
It watches customer folders, analyzes incoming files, decides how each file
should be handled, creates reusable mappings, and exchanges files with
Modula WMS through the local IMPEXP folder.

Inbound flow:
1. Customer places a file in runtime/customer_input
2. AI middleware classifies the file
3. AI middleware creates or reuses a mapping profile
4. Runtime converts customer order data into IMP_ORDINI XML
5. Runtime writes XML into C:\SystemLogistics\IMPEXP

Outbound flow:
1. Runtime watches C:\SystemLogistics\IMPEXP for EXP_ORDINI XML
2. Runtime converts EXP_ORDINI XML into customer CSV
3. Runtime writes the CSV into runtime/customer_output
"""

import csv
import json
import shutil
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from agents.openai_mapping_agent import infer_mapping_with_openai
except Exception:
    infer_mapping_with_openai = None


CUSTOMER_NAME = "Quick Test Customer"
BASE_FOLDER = Path(__file__).resolve().parent

RUNTIME_FOLDER = BASE_FOLDER / "runtime"
INPUT_FOLDER = RUNTIME_FOLDER / "customer_input"
OUTPUT_FOLDER = RUNTIME_FOLDER / "modula_output"
CUSTOMER_OUTPUT_FOLDER = RUNTIME_FOLDER / "customer_output"
PROCESSED_FOLDER = RUNTIME_FOLDER / "processed"
ERROR_FOLDER = RUNTIME_FOLDER / "errors"
PROFILE_FOLDER = RUNTIME_FOLDER / "profiles"
WMS_EXPORT_PROCESSED_FOLDER = RUNTIME_FOLDER / "wms_export_processed"
DECISION_LOG_FOLDER = RUNTIME_FOLDER / "decision_logs"

WMS_IMPEXP_FOLDER = Path(r"C:\SystemLogistics\IMPEXP")
POLL_SECONDS = 5
FILE_STABILITY_SECONDS = 2

CANONICAL_ORDER_FIELDS = [
    "order_id",
    "customer_name",
    "item",
    "quantity",
]

SUPPORTED_INBOUND_EXTENSIONS = [".csv"]


# ==================================================
# Runtime setup
# ==================================================
def ensure_runtime_folders() -> None:
    for folder in [
        INPUT_FOLDER,
        OUTPUT_FOLDER,
        CUSTOMER_OUTPUT_FOLDER,
        PROCESSED_FOLDER,
        ERROR_FOLDER,
        PROFILE_FOLDER,
        WMS_EXPORT_PROCESSED_FOLDER,
        DECISION_LOG_FOLDER,
        WMS_IMPEXP_FOLDER,
    ]:
        folder.mkdir(parents=True, exist_ok=True)


def get_safe_customer_name(customer_name: str) -> str:
    return customer_name.strip().lower().replace(" ", "_")


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def write_json_file(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def log_decision(decision: dict) -> Path:
    log_path = DECISION_LOG_FOLDER / f"decision_{{timestamp()}}.json"
    write_json_file(log_path, decision)
    return log_path


def is_file_stable(file_path: Path) -> bool:
    first_size = file_path.stat().st_size
    time.sleep(FILE_STABILITY_SECONDS)
    second_size = file_path.stat().st_size
    return first_size == second_size


# ==================================================
# Profiles
# ==================================================
def get_profile_path(customer_name: str, document_type: str = "ordini") -> Path:
    safe_name = get_safe_customer_name(customer_name)
    return PROFILE_FOLDER / f"{{safe_name}}_{{document_type}}_profile.json"


def load_profile(customer_name: str, document_type: str = "ordini") -> dict | None:
    profile_path = get_profile_path(customer_name, document_type)

    if not profile_path.exists():
        return None

    with open(profile_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_profile(
    customer_name: str,
    document_type: str,
    source_type: str,
    mapping: dict,
) -> Path:
    profile_path = get_profile_path(customer_name, document_type)

    profile = {
        "customer_name": customer_name,
        "source_type": source_type,
        "document_type": document_type,
        "output_format": "modula_wms_xml",
        "field_mappings": mapping,
        "created_at": datetime.now().isoformat(),
        "mapping_confirmation_required": False,
        "created_by": "ai_middleware_agent",
    }

    write_json_file(profile_path, profile)
    return profile_path


# ==================================================
# AI middleware decisioning
# ==================================================
def read_csv_preview(file_path: Path) -> tuple[list[str], list[dict]]:
    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    return reader.fieldnames or [], rows[:5]


def classify_inbound_file(file_path: Path) -> dict:
    """
    Classify the inbound file and decide which middleware action to run.

    This currently supports CSV order files. The function is intentionally
    structured as an agent decision point so future support can be added for
    inventory, items/articles, JSON, XML, Excel, SQL, REST API, or EDI.
    """
    suffix = file_path.suffix.lower()

    decision = {
        "customer_name": CUSTOMER_NAME,
        "file_path": str(file_path),
        "file_name": file_path.name,
        "source_type": suffix.replace(".", ""),
        "document_type": "unknown",
        "middleware_action": "unsupported",
        "reason": "File type or document type not recognized.",
        "decided_at": datetime.now().isoformat(),
    }

    if suffix not in SUPPORTED_INBOUND_EXTENSIONS:
        return decision

    headers, preview_rows = read_csv_preview(file_path)
    lowered_headers = [header.lower().strip() for header in headers]

    order_signals = [
        "order",
        "order_id",
        "order_number",
        "po",
        "po_number",
        "ord_ordine",
        "item",
        "sku",
        "part",
        "quantity",
        "qty",
        "rig_articolo",
        "rig_qtar",
    ]

    score = 0
    for header in lowered_headers:
        for signal in order_signals:
            if signal in header:
                score += 1

    if score >= 2:
        decision.update(
            {
                "document_type": "ordini",
                "middleware_action": "convert_customer_orders_to_modula_xml",
                "reason": "CSV headers look like customer order data.",
                "headers": headers,
                "sample_rows": preview_rows,
            }
        )

    return decision


def heuristic_order_mapping(headers: list[str]) -> dict:
    mapping = {field: None for field in CANONICAL_ORDER_FIELDS}

    for header in headers:
        clean = header.lower().strip()

        if clean in [
            "order_id",
            "order",
            "order_number",
            "ord_ordine",
            "po",
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


def suggest_order_mapping(headers: list[str], sample_rows: list[dict]) -> dict:
    if infer_mapping_with_openai is None:
        print("OpenAI mapping agent unavailable. Using heuristic fallback.")
        return heuristic_order_mapping(headers)

    try:
        print("
AI middleware is generating an order mapping...")

        ai_mapping = infer_mapping_with_openai(
            columns=headers,
            sample_rows=sample_rows,
        )

        mapping = {field: ai_mapping.get(field) for field in CANONICAL_ORDER_FIELDS}

        print("AI mapping suggestion received.")
        return mapping

    except Exception as error:
        print(f"AI mapping failed. Using heuristic fallback: {{error}}")
        return heuristic_order_mapping(headers)


def validate_order_mapping(headers: list[str], suggested_mapping: dict) -> dict:
    print("
Validating middleware mapping...")
    print(json.dumps(suggested_mapping, indent=4))

    missing = [
        field
        for field in CANONICAL_ORDER_FIELDS
        if not suggested_mapping.get(field)
    ]

    if missing:
        raise ValueError(f"Mapping failed. Missing required fields: {{missing}}")

    invalid_columns = [
        source_column
        for source_column in suggested_mapping.values()
        if source_column not in headers
    ]

    if invalid_columns:
        raise ValueError(f"Mapping failed. Invalid source columns: {{invalid_columns}}")

    return suggested_mapping


def get_or_create_order_mapping(headers: list[str], sample_rows: list[dict]) -> dict:
    profile = load_profile(CUSTOMER_NAME, "ordini")

    if profile:
        mapping = profile["field_mappings"]

        try:
            return validate_order_mapping(headers, mapping)
        except Exception as error:
            print(f"Saved profile no longer matches this file: {{error}}")
            print("AI middleware will regenerate the mapping.")

    suggested_mapping = suggest_order_mapping(headers, sample_rows)
    mapping = validate_order_mapping(headers, suggested_mapping)

    profile_path = save_profile(
        customer_name=CUSTOMER_NAME,
        document_type="ordini",
        source_type="csv",
        mapping=mapping,
    )

    print(f"Saved AI middleware profile: {{profile_path}}")
    return mapping


# ==================================================
# Modula XML conversion
# ==================================================
def add_text(parent: ET.Element, tag: str, value: Any = "") -> ET.Element:
    element = ET.SubElement(parent, tag)
    element.text = str(value) if value is not None else ""
    return element


def convert_csv_orders_to_modula_xml(
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
            description = row.get(mapping["customer_name"], "").strip()

            orders_by_id[order_id] = {
                "order_id": order_id,
                "description": description or order_id,
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
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

    return {
        "status": "success",
        "customer_name": CUSTOMER_NAME,
        "source_file": str(file_path),
        "orders_converted": len(orders_by_id),
        "rows_converted": len(rows),
        "output_path": str(output_path),
    }


# ==================================================
# File movement
# ==================================================
def move_file(source_path: Path, target_folder: Path) -> Path:
    target_folder.mkdir(parents=True, exist_ok=True)
    target_path = target_folder / source_path.name

    if target_path.exists():
        target_path = target_folder / f"{{source_path.stem}}_{{timestamp()}}{{source_path.suffix}}"

    shutil.move(str(source_path), str(target_path))
    return target_path


def copy_file(source_path: Path, target_folder: Path) -> Path:
    target_folder.mkdir(parents=True, exist_ok=True)
    target_path = target_folder / source_path.name

    if target_path.exists():
        target_path = target_folder / f"{{source_path.stem}}_{{timestamp()}}{{source_path.suffix}}"

    shutil.copy2(str(source_path), str(target_path))
    return target_path


# ==================================================
# Inbound middleware processing
# ==================================================
def process_customer_file(file_path: Path) -> dict:
    print(f"
AI middleware analyzing customer file: {{file_path}}")

    if not is_file_stable(file_path):
        raise ValueError("File is still being copied. It will be retried later.")

    decision = classify_inbound_file(file_path)
    decision_log_path = log_decision(decision)

    print("Middleware decision:")
    print(json.dumps(decision, indent=4, default=str))
    print(f"Decision log: {{decision_log_path}}")

    if decision["middleware_action"] != "convert_customer_orders_to_modula_xml":
        raise ValueError(decision["reason"])

    headers = decision.get("headers") or []
    sample_rows = decision.get("sample_rows") or []

    mapping = get_or_create_order_mapping(headers, sample_rows)

    import_filename = f"IMP_ORDINI_{{file_path.stem}}_{{timestamp()}}.xml"
    wms_import_path = WMS_IMPEXP_FOLDER / import_filename

    result = convert_csv_orders_to_modula_xml(
        file_path=file_path,
        mapping=mapping,
        output_path=wms_import_path,
    )

    archive_copy_path = copy_file(wms_import_path, OUTPUT_FOLDER)
    processed_path = move_file(file_path, PROCESSED_FOLDER)

    result.update(
        {
            "middleware_action": decision["middleware_action"],
            "document_type": decision["document_type"],
            "wms_import_path": str(wms_import_path),
            "archive_copy_path": str(archive_copy_path),
            "processed_path": str(processed_path),
        }
    )

    print("AI middleware inbound processing complete:")
    print(json.dumps(result, indent=4))

    return result


# ==================================================
# WMS export processing
# ==================================================
def is_wms_export_file(file_path: Path) -> bool:
    return (
        file_path.is_file()
        and file_path.suffix.lower() == ".xml"
        and file_path.name.upper().startswith("EXP_ORDINI")
    )


def get_xml_text(parent: ET.Element, tag: str) -> str:
    element = parent.find(tag)

    if element is None or element.text is None:
        return ""

    return element.text.strip()


def convert_exp_ordini_xml_to_customer_csv(
    export_path: Path,
    output_path: Path,
) -> dict:
    tree = ET.parse(export_path)
    root = tree.getroot()
    rows = []

    for order_element in root.findall("EXP_ORDINI"):
        order_id = get_xml_text(order_element, "ORD_ORDINE")
        order_type = get_xml_text(order_element, "ORD_TIPOOP")
        warehouse_number = get_xml_text(order_element, "ORD_ATTR1")
        elebaie = get_xml_text(order_element, "ORD_ELEBAIE")

        for line_element in order_element.findall("EXP_ORDINI_RIGHE"):
            rows.append(
                {
                    "order_id": get_xml_text(line_element, "RIG_ORDINE") or order_id,
                    "operation_type": order_type,
                    "warehouse_number": warehouse_number,
                    "elebaie": elebaie,
                    "item": get_xml_text(line_element, "RIG_ARTICOLO"),
                    "batch": get_xml_text(line_element, "RIG_SUB1"),
                    "warehouse_task": get_xml_text(line_element, "RIG_ATTR1"),
                    "source_storage_bin": get_xml_text(line_element, "RIG_ATTR2"),
                    "destination_storage_bin": get_xml_text(line_element, "RIG_ATTR3"),
                    "quantity_exported": get_xml_text(line_element, "RIG_QTAE"),
                }
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "order_id",
        "operation_type",
        "warehouse_number",
        "elebaie",
        "item",
        "batch",
        "warehouse_task",
        "source_storage_bin",
        "destination_storage_bin",
        "quantity_exported",
    ]

    with open(output_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return {
        "status": "success",
        "customer_name": CUSTOMER_NAME,
        "source_export_file": str(export_path),
        "rows_exported": len(rows),
        "output_path": str(output_path),
    }


def process_wms_export_file(file_path: Path) -> dict:
    print(f"
AI middleware processing WMS export: {{file_path}}")

    if not is_file_stable(file_path):
        raise ValueError("WMS export file is still being written. It will be retried later.")

    output_path = CUSTOMER_OUTPUT_FOLDER / f"{{file_path.stem}}_customer_{{timestamp()}}.csv"

    result = convert_exp_ordini_xml_to_customer_csv(
        export_path=file_path,
        output_path=output_path,
    )

    processed_path = move_file(file_path, WMS_EXPORT_PROCESSED_FOLDER)
    result["processed_wms_export_path"] = str(processed_path)

    print("AI middleware outbound processing complete:")
    print(json.dumps(result, indent=4))

    return result


# ==================================================
# Runtime loops
# ==================================================
def scan_customer_inputs_once() -> None:
    ensure_runtime_folders()

    for file_path in sorted(INPUT_FOLDER.iterdir()):
        if not file_path.is_file():
            continue

        try:
            process_customer_file(file_path)

        except Exception as error:
            print(f"ERROR processing customer file {{file_path}}: {{error}}")

            if file_path.exists():
                move_file(file_path, ERROR_FOLDER)


def scan_wms_exports_once() -> None:
    ensure_runtime_folders()

    for file_path in sorted(WMS_IMPEXP_FOLDER.iterdir()):
        if not is_wms_export_file(file_path):
            continue

        try:
            process_wms_export_file(file_path)

        except Exception as error:
            print(f"ERROR processing WMS export {{file_path}}: {{error}}")

            if file_path.exists():
                move_file(file_path, ERROR_FOLDER)


def scan_once() -> None:
    scan_customer_inputs_once()
    scan_wms_exports_once()


def run_forever() -> None:
    ensure_runtime_folders()

    print("=" * 70)
    print("MODULA AI MIDDLEWARE AGENT STARTED")
    print("=" * 70)
    print(f"Customer: {{CUSTOMER_NAME}}")
    print(f"Customer Input Folder: {{INPUT_FOLDER}}")
    print(f"WMS IMPEXP Folder: {{WMS_IMPEXP_FOLDER}}")
    print(f"Customer Output Folder: {{CUSTOMER_OUTPUT_FOLDER}}")
    print(f"Import XML Archive Folder: {{OUTPUT_FOLDER}}")
    print(f"Processed Customer Files: {{PROCESSED_FOLDER}}")
    print(f"Processed WMS Exports: {{WMS_EXPORT_PROCESSED_FOLDER}}")
    print(f"Decision Logs: {{DECISION_LOG_FOLDER}}")
    print(f"Errors: {{ERROR_FOLDER}}")
    print("=" * 70)

    while True:
        scan_once()
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    run_forever()
