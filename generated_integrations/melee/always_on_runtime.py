"""
always_on_runtime.py — Melee AI Middleware Runtime

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


def flatten_export_orders(export_orders: list[dict]) -> list[dict]:
    # Flatten order/line data for CSV output.
    rows = []

    for order in export_orders:
        for line in order.get("lines", []):
            rows.append(
                {
                    "order_id": order.get("order_id", ""),
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


def write_customer_export_json(export_orders: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "source_system": "Modula WMS",
        "document_type": "EXP_ORDINI",
        "exported_at": datetime.now().isoformat(),
        "orders": export_orders,
    }

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=4)


def write_customer_export_csv(export_orders: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = flatten_export_orders(export_orders)
    fieldnames = [
        "order_id",
        "operation_type",
        "warehouse_number",
        "bay_number",
        "item",
        "quantity",
        "sub1",
        "warehouse_task",
        "source_bin",
        "destination_bin",
    ]

    with open(output_path, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_customer_export_xml(export_orders: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    root = ET.Element("orders")

    for order in export_orders:
        order_element = ET.SubElement(root, "order")
        add_text(order_element, "order_id", order.get("order_id", ""))
        add_text(order_element, "operation_type", order.get("operation_type", ""))
        add_text(order_element, "warehouse_number", order.get("warehouse_number", ""))
        add_text(order_element, "bay_number", order.get("bay_number", ""))

        lines_element = ET.SubElement(order_element, "lines")

        for line in order.get("lines", []):
            line_element = ET.SubElement(lines_element, "line")
            add_text(line_element, "item", line.get("item", ""))
            add_text(line_element, "quantity", line.get("quantity", ""))
            add_text(line_element, "sub1", line.get("sub1", ""))
            add_text(line_element, "warehouse_task", line.get("warehouse_task", ""))
            add_text(line_element, "source_bin", line.get("source_bin", ""))
            add_text(line_element, "destination_bin", line.get("destination_bin", ""))

    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ", level=0)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


def write_customer_export(export_orders: list[dict], source_file: Path) -> Path:
    # Convert parsed EXP_ORDINI data back into the customer's configured format.
    output_format = CUSTOMER_OUTPUT_FORMAT

    if output_format not in ["json", "csv", "xml"]:
        log.warning(
            f"Unsupported customer output format '{output_format}'; defaulting to JSON."
        )
        output_format = "json"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = CUSTOMER_OUTPUT_DIR / f"{source_file.stem}_customer_export_{timestamp}.{output_format}"

    if output_format == "csv":
        write_customer_export_csv(export_orders, output_path)
    elif output_format == "xml":
        write_customer_export_xml(export_orders, output_path)
    else:
        write_customer_export_json(export_orders, output_path)

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
    log.info("  Melee AI Middleware Runtime")
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
