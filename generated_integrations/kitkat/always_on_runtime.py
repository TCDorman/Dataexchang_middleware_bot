"""
always_on_runtime.py — KitKat AI Middleware Runtime

Portable runtime package.

Import side:
- Watches runtime/customer_input for CSV, JSON, and XML customer order files.
- Converts customer order files into Modula IMP_ORDINI XML.
- Copies generated XML into the configured Modula IMPEXP folder.

Export side:
- Watches the configured Modula IMPEXP folder for EXP_ORDINI XML files.
- Converts Modula export order confirmations back into the customer's format.
- Writes customer-facing output files to runtime/customer_output.
"""

import csv
import json
import logging
import shutil
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent

if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

log = logging.getLogger("runtime")


CONFIG_PATH = PACKAGE_DIR / "config.json"
DEFAULT_SUPPORTED_EXTENSIONS = [".csv", ".json", ".xml"]
DEFAULT_CUSTOMER_OUTPUT_FORMAT = "json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing config file: {CONFIG_PATH}")

    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def resolve_package_path(path_value: str) -> Path:
    path = Path(path_value)

    if path.is_absolute():
        return path

    return PACKAGE_DIR / path


CONFIG = load_config()
RUNTIME_CONFIG = CONFIG.get("runtime", {})
WMS_CONFIG = CONFIG.get("wms", {})
CUSTOMER_OUTPUT_CONFIG = CONFIG.get("customer_output", {})

INPUT_DIR = resolve_package_path(
    RUNTIME_CONFIG.get("input_dir", "runtime/customer_input")
)
CUSTOMER_OUTPUT_DIR = resolve_package_path(
    RUNTIME_CONFIG.get("output_dir", "runtime/customer_output")
)
MODULA_OUT_DIR = resolve_package_path(
    RUNTIME_CONFIG.get("modula_output_dir", "runtime/modula_output")
)
PROCESSED_DIR = resolve_package_path(
    RUNTIME_CONFIG.get("processed_dir", "runtime/processed")
)
ERRORS_DIR = resolve_package_path(
    RUNTIME_CONFIG.get("errors_dir", "runtime/errors")
)
PROFILES_DIR = resolve_package_path(
    RUNTIME_CONFIG.get("profiles_dir", "runtime/profiles")
)
WMS_EXPORT_PROCESSED_DIR = resolve_package_path(
    RUNTIME_CONFIG.get("wms_export_processed_dir", "runtime/wms_export_processed")
)

WMS_ORDER_IMPORT_DIR = resolve_package_path(
    WMS_CONFIG.get("ordini_import_path", "runtime/wms_order_import_test")
)
WMS_EXPORT_WATCH_DIR = resolve_package_path(
    WMS_CONFIG.get(
        "export_watch_path",
        WMS_CONFIG.get("ordini_import_path", "runtime/wms_order_import_test"),
    )
)

SUPPORTED_EXTENSIONS = [
    ext.lower()
    for ext in CONFIG.get("supported_file_extensions", DEFAULT_SUPPORTED_EXTENSIONS)
]
CUSTOMER_OUTPUT_FORMAT = CUSTOMER_OUTPUT_CONFIG.get(
    "format",
    CONFIG.get("source_type", DEFAULT_CUSTOMER_OUTPUT_FORMAT),
).lower()
POLL_INTERVAL = int(RUNTIME_CONFIG.get("poll_interval_seconds", 5))


try:
    from src.pipeline.file_processing_pipeline import FileProcessingPipeline
except ImportError as error:
    log.error(f"Could not import FileProcessingPipeline: {error}")
    log.error("This portable package must include src/ and agents/ folders.")
    sys.exit(1)


def ensure_runtime_folders() -> None:
    for folder in [
        INPUT_DIR,
        CUSTOMER_OUTPUT_DIR,
        MODULA_OUT_DIR,
        PROCESSED_DIR,
        ERRORS_DIR,
        PROFILES_DIR,
        WMS_ORDER_IMPORT_DIR,
        WMS_EXPORT_WATCH_DIR,
        WMS_EXPORT_PROCESSED_DIR,
    ]:
        folder.mkdir(parents=True, exist_ok=True)


def safe_move(source_path: Path, target_folder: Path) -> Path:
    # Move a file without overwriting an existing file.
    target_folder.mkdir(parents=True, exist_ok=True)
    target_path = target_folder / source_path.name

    if target_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_path = target_folder / f"{source_path.stem}_{timestamp}{source_path.suffix}"

    shutil.move(str(source_path), str(target_path))
    return target_path


def copy_xml_to_wms_import(xml_output: Path) -> Path:
    WMS_ORDER_IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    destination = WMS_ORDER_IMPORT_DIR / xml_output.name
    shutil.copy2(xml_output, destination)
    return destination


def add_text(parent: ET.Element, tag: str, value: object = "") -> ET.Element:
    element = ET.SubElement(parent, tag)
    element.text = "" if value is None else str(value)
    return element


def clean_text(value: str | None) -> str:
    return value.strip() if value else ""


def is_supported_input_file(file_path: Path) -> bool:
    # Customer input files can be CSV, JSON, or XML.
    return file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS


def is_possible_export_ordini_file(file_path: Path) -> bool:
    # Modula export files are XML. Content is checked for EXP_ORDINI later.
    return file_path.is_file() and file_path.suffix.lower() == ".xml"


def parse_export_ordini_xml(file_path: Path) -> list[dict]:
    # Parse Modula EXP_ORDINI XML into a customer-neutral export structure.
    tree = ET.parse(file_path)
    root = tree.getroot()

    export_orders = []

    for order_node in root.findall(".//EXP_ORDINI"):
        order_number = clean_text(order_node.findtext("ORD_ORDINE"))

        order = {
            "order_id": order_number,
            "operation_type": clean_text(order_node.findtext("ORD_TIPOOP")),
            "warehouse_number": clean_text(order_node.findtext("ORD_ATTR1")),
            "bay_number": clean_text(order_node.findtext("ORD_ELEBAIE")),
            "lines": [],
        }

        for line_node in order_node.findall(".//EXP_ORDINI_RIGHE"):
            order["lines"].append(
                {
                    "order_id": clean_text(line_node.findtext("RIG_ORDINE")) or order_number,
                    "item": clean_text(line_node.findtext("RIG_ARTICOLO")),
                    "quantity": clean_text(line_node.findtext("RIG_QTAE")),
                    "sub1": clean_text(line_node.findtext("RIG_SUB1")),
                    "warehouse_task": clean_text(line_node.findtext("RIG_ATTR1")),
                    "source_bin": clean_text(line_node.findtext("RIG_ATTR2")),
                    "destination_bin": clean_text(line_node.findtext("RIG_ATTR3")),
                }
            )

        export_orders.append(order)

    return export_orders


def get_profile_files() -> list[Path]:
    # Profiles are created by the import side after OpenAI/user mapping.
    return sorted(PROFILES_DIR.glob("*_profile.json"))


def load_customer_profile() -> dict:
    # Load the best available customer profile.
    #
    # The export side uses this saved profile to rebuild the customer's original
    # column/tag names. This is the same mapping created during customer import.
    configured_customer = CONFIG.get("customer_name", "")
    safe_customer = configured_customer.strip().lower().replace(" ", "_")

    candidate_paths = []

    if safe_customer:
        candidate_paths.append(PROFILES_DIR / f"{safe_customer}_profile.json")

    candidate_paths.extend(get_profile_files())

    for profile_path in candidate_paths:
        if not profile_path.exists():
            continue

        try:
            with open(profile_path, "r", encoding="utf-8") as file:
                profile = json.load(file)

            log.info(f"Loaded customer profile for export mapping: {profile_path.name}")
            return profile

        except Exception as error:
            log.warning(f"Could not load profile {profile_path}: {error}")

    log.warning(
        "No saved customer profile found. Export will use generic field names."
    )
    return {}


def get_profile_field_mapping(profile: dict) -> dict:
    # Return the internal-field to customer-field mapping.
    #
    # Different parts of the project have used both names:
    # - field_mapping
    # - field_mappings
    #
    # This helper supports both so older saved profiles still work.
    mapping = (
        profile.get("field_mapping")
        or profile.get("field_mappings")
        or {}
    )

    if not isinstance(mapping, dict):
        return {}

    return mapping


def customer_field_name(field_mapping: dict, internal_field: str) -> str:
    # Convert an internal canonical field into the customer's original field name.
    #
    # Example:
    #     internal: item
    #     customer field from profile: Part Number
    mapped_name = field_mapping.get(internal_field)

    if mapped_name:
        return str(mapped_name)

    fallback_names = {
        "order_id": "order_id",
        "customer_name": "customer_name",
        "item": "item",
        "quantity": "quantity",
        "operation_type": "operation_type",
        "warehouse_number": "warehouse_number",
        "bay_number": "bay_number",
        "sub1": "sub1",
        "warehouse_task": "warehouse_task",
        "source_bin": "source_bin",
        "destination_bin": "destination_bin",
    }

    return fallback_names.get(internal_field, internal_field)


def flatten_export_orders(export_orders: list[dict]) -> list[dict]:
    # Flatten order/line data into the same canonical structure used by imports.
    rows = []

    for order in export_orders:
        for line in order.get("lines", []):
            rows.append(
                {
                    "order_id": order.get("order_id", ""),
                    "customer_name": order.get("customer_name", ""),
                    "operation_type": order.get("operation_type", ""),
                    "warehouse_number": order.get("warehouse_number", ""),
                    "bay_number": order.get("bay_number", ""),
                    "item": line.get("item", ""),
                    "quantity": line.get("quantity", ""),
                    "sub1": line.get("sub1", ""),
                    "warehouse_task": line.get("warehouse_task", ""),
                    "source_bin": line.get("source_bin", ""),
                    "destination_bin": line.get("destination_bin", ""),
                }
            )

    return rows


def map_export_rows_to_customer_fields(
    export_orders: list[dict],
    field_mapping: dict,
) -> list[dict]:
    # Apply the saved OpenAI/customer profile mapping to export rows.
    #
    # The import side maps customer fields -> internal fields.
    # The export side maps internal fields -> customer fields.
    canonical_rows = flatten_export_orders(export_orders)

    customer_rows = []

    for row in canonical_rows:
        customer_row = {
            customer_field_name(field_mapping, "order_id"): row.get("order_id", ""),
            customer_field_name(field_mapping, "customer_name"): row.get("customer_name", ""),
            customer_field_name(field_mapping, "item"): row.get("item", ""),
            customer_field_name(field_mapping, "quantity"): row.get("quantity", ""),
        }

        # Extra WMS export details are appended with stable fallback names unless
        # the profile has explicit names for them.
        for extra_field in [
            "operation_type",
            "warehouse_number",
            "bay_number",
            "sub1",
            "warehouse_task",
            "source_bin",
            "destination_bin",
        ]:
            customer_row[customer_field_name(field_mapping, extra_field)] = row.get(
                extra_field,
                "",
            )

        customer_rows.append(customer_row)

    return customer_rows


def is_blank_export_value(value: object) -> bool:
    # Treat None and whitespace-only strings as empty export values.
    # This helper is used by CSV, JSON, and XML output cleanup.
    return value is None or str(value).strip() == ""


def clean_customer_export_rows(customer_rows: list[dict]) -> list[dict]:
    # Remove fields that are blank across every exported row.
    #
    # Example: if Company, warehouse_number, bay_number, and source_bin are blank
    # in all rows, they are removed from JSON/XML/CSV output entirely. If a field
    # has a value in at least one row, it is kept and blank values in individual
    # rows are skipped for JSON/XML.
    if not customer_rows:
        return []

    fieldnames = list(customer_rows[0].keys())

    fields_with_any_value = [
        field
        for field in fieldnames
        if any(not is_blank_export_value(row.get(field)) for row in customer_rows)
    ]

    cleaned_rows = []

    for row in customer_rows:
        cleaned_row = {
            field: row.get(field, "")
            for field in fields_with_any_value
            if not is_blank_export_value(row.get(field))
        }

        cleaned_rows.append(cleaned_row)

    return cleaned_rows


def group_customer_rows_for_json(customer_rows: list[dict], field_mapping: dict) -> list[dict]:
    # Build customer-shaped JSON using the customer's mapped field names.
    #
    # Empty fields are removed before grouping so JSON does not include blank
    # keys like Company, warehouse_number, bay_number, source_bin, etc.
    order_field = customer_field_name(field_mapping, "order_id")
    customer_field = customer_field_name(field_mapping, "customer_name")

    cleaned_rows = clean_customer_export_rows(customer_rows)
    grouped_orders = {}

    for row in cleaned_rows:
        order_id = row.get(order_field, "")

        if not order_id:
            continue

        if order_id not in grouped_orders:
            grouped_order = {
                order_field: order_id,
                "lines": [],
            }

            if customer_field in row and not is_blank_export_value(row.get(customer_field)):
                grouped_order[customer_field] = row.get(customer_field, "")

            grouped_orders[order_id] = grouped_order

        line_payload = {}

        for key, value in row.items():
            if key in [order_field, customer_field]:
                continue

            if is_blank_export_value(value):
                continue

            # Keep item and quantity using customer field names, and keep any
            # non-empty WMS export metadata as additional fields.
            line_payload[key] = value

        if line_payload:
            grouped_orders[order_id]["lines"].append(line_payload)

    return list(grouped_orders.values())


def write_customer_export_json(
    export_orders: list[dict],
    output_path: Path,
    field_mapping: dict,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    customer_rows = map_export_rows_to_customer_fields(export_orders, field_mapping)

    payload = {
        "source_system": "Modula WMS",
        "document_type": "EXP_ORDINI",
        "exported_at": datetime.now().isoformat(),
        "orders": group_customer_rows_for_json(customer_rows, field_mapping),
    }

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=4)


def write_customer_export_csv(
    export_orders: list[dict],
    output_path: Path,
    field_mapping: dict,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = map_export_rows_to_customer_fields(export_orders, field_mapping)

    if rows:
        fieldnames = list(rows[0].keys())
    else:
        fieldnames = [
            customer_field_name(field_mapping, "order_id"),
            customer_field_name(field_mapping, "customer_name"),
            customer_field_name(field_mapping, "item"),
            customer_field_name(field_mapping, "quantity"),
        ]

    # Drop CSV columns that are empty for every exported row.
    # This keeps the customer export clean instead of sending blank WMS metadata
    # columns like warehouse_number, bay_number, source_bin, etc.
    if rows:
        fieldnames = [
            field
            for field in fieldnames
            if any(str(row.get(field, "")).strip() for row in rows)
        ]

    # Safety fallback: if every field is somehow blank, keep the core customer
    # fields so the CSV still has a usable structure.
    if not fieldnames:
        fieldnames = [
            customer_field_name(field_mapping, "order_id"),
            customer_field_name(field_mapping, "item"),
            customer_field_name(field_mapping, "quantity"),
        ]

    # DictWriter raises an error if rows contain keys not listed in fieldnames.
    # extrasaction="ignore" lets us omit fully blank columns safely.
    with open(output_path, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_customer_export_xml(
    export_orders: list[dict],
    output_path: Path,
    field_mapping: dict,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    customer_rows = map_export_rows_to_customer_fields(export_orders, field_mapping)
    cleaned_rows = clean_customer_export_rows(customer_rows)
    root = ET.Element("orders")

    for row in cleaned_rows:
        row_element = ET.SubElement(root, "order")

        for field_name, value in row.items():
            # Skip blank values so the XML does not contain empty tags like
            # <Company />, <warehouse_number />, <source_bin />, etc.
            if is_blank_export_value(value):
                continue

            # XML tags cannot safely contain spaces or punctuation. The profile
            # can include friendly customer column names, so normalize them for XML.
            safe_tag = (
                str(field_name)
                .strip()
                .replace(" ", "_")
                .replace("-", "_")
                .replace("/", "_")
            )

            if not safe_tag:
                safe_tag = "field"

            add_text(row_element, safe_tag, value)

    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ", level=0)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


def write_customer_export(export_orders: list[dict], source_file: Path) -> Path:
    # Convert parsed EXP_ORDINI data back into the customer's configured format.
    output_format = CUSTOMER_OUTPUT_FORMAT
    profile = load_customer_profile()
    field_mapping = get_profile_field_mapping(profile)

    if field_mapping:
        log.info(f"Using profile-driven export mapping: {field_mapping}")
    else:
        log.warning("Using generic export mapping because no field mapping was found.")

    if output_format not in ["json", "csv", "xml"]:
        log.warning(
            f"Unsupported customer output format '{output_format}'; defaulting to JSON."
        )
        output_format = "json"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = CUSTOMER_OUTPUT_DIR / f"{source_file.stem}_customer_export_{timestamp}.{output_format}"

    if output_format == "csv":
        write_customer_export_csv(export_orders, output_path, field_mapping)
    elif output_format == "xml":
        write_customer_export_xml(export_orders, output_path, field_mapping)
    else:
        write_customer_export_json(export_orders, output_path, field_mapping)

    return output_path



def process_customer_input_file(pipeline: FileProcessingPipeline, file_path: Path) -> None:
    # Process customer-originated order files into Modula IMP_ORDINI XML.
    source_type = file_path.suffix.lower().lstrip(".")
    log.info(f"Detected customer {source_type.upper()}: {file_path.name}")
    result = pipeline.process(file_path=file_path)

    if result.get("status") == "success":
        xml_output = Path(result.get("xml_output"))
        wms_destination = copy_xml_to_wms_import(xml_output)

        log.info(
            f"IMPORT SUCCESS type={result.get('source_type')} "
            f"orders={result.get('orders_processed')} "
            f"xml={xml_output.name}"
        )
        log.info(f"WMS import copy: {wms_destination}")
    else:
        log.error(f"IMPORT FAILED {result.get('error')}")


def process_export_ordini_file(file_path: Path) -> None:
    # Process Modula-originated EXP_ORDINI XML back into customer output.
    log.info(f"Checking WMS export file: {file_path.name}")

    export_orders = parse_export_ordini_xml(file_path)

    if not export_orders:
        # Most often this is one of our IMP_ORDINI files in the shared IMPEXP
        # folder. Leave it alone so Modula can consume it.
        log.info(f"Skipping XML without EXP_ORDINI nodes: {file_path.name}")
        return

    output_path = write_customer_export(export_orders, file_path)
    processed_path = safe_move(file_path, WMS_EXPORT_PROCESSED_DIR)

    line_count = sum(len(order.get("lines", [])) for order in export_orders)

    log.info(
        f"EXPORT SUCCESS orders={len(export_orders)} "
        f"lines={line_count} output={output_path.name}"
    )
    log.info(f"Customer output written: {output_path}")
    log.info(f"WMS export moved to: {processed_path}")


def main() -> None:
    ensure_runtime_folders()

    pipeline = FileProcessingPipeline(
        profiles_dir=PROFILES_DIR,
        modula_output_dir=MODULA_OUT_DIR,
        processed_dir=PROCESSED_DIR,
        errors_dir=ERRORS_DIR,
    )

    log.info("=" * 60)
    log.info("  KitKat AI Middleware Runtime")
    log.info("=" * 60)
    log.info(f"  Package          : {PACKAGE_DIR}")
    log.info(f"  Customer input   : {INPUT_DIR}")
    log.info(f"  Modula XML out   : {MODULA_OUT_DIR}")
    log.info(f"  WMS IMPEXP       : {WMS_ORDER_IMPORT_DIR}")
    log.info(f"  WMS export watch : {WMS_EXPORT_WATCH_DIR}")
    log.info(f"  Customer output  : {CUSTOMER_OUTPUT_DIR}")
    log.info(f"  Output format    : {CUSTOMER_OUTPUT_FORMAT}")
    log.info(f"  Processed        : {PROCESSED_DIR}")
    log.info(f"  Errors           : {ERRORS_DIR}")
    log.info(f"  Profiles         : {PROFILES_DIR}")
    log.info(f"  Supported input  : {', '.join(SUPPORTED_EXTENSIONS)}")
    log.info("  Drop CSV/JSON/XML customer files into customer_input.")
    log.info("  Drop or wait for Modula EXP_ORDINI XML files in the WMS IMPEXP folder.")
    log.info("=" * 60)

    seen_customer_inputs = set()
    seen_wms_exports = set()

    while True:
        try:
            customer_files = list(INPUT_DIR.iterdir())

            for file_path in customer_files:
                if not is_supported_input_file(file_path):
                    continue

                if file_path.name in seen_customer_inputs:
                    continue

                seen_customer_inputs.add(file_path.name)
                process_customer_input_file(pipeline, file_path)

            wms_files = list(WMS_EXPORT_WATCH_DIR.iterdir())

            for file_path in wms_files:
                if not is_possible_export_ordini_file(file_path):
                    continue

                if file_path.name in seen_wms_exports:
                    continue

                seen_wms_exports.add(file_path.name)
                process_export_ordini_file(file_path)

            if not customer_files and not wms_files:
                log.info("Waiting... no customer input or WMS export files found")

        except KeyboardInterrupt:
            log.info("Shutdown requested — stopping runtime.")
            break

        except Exception as error:
            log.error(f"Watcher error: {error}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
