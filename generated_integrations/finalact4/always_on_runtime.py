"""
always_on_runtime.py — FinalACT4 AI Middleware Runtime

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
REST_API_CONFIG = CONFIG.get("rest_api", {})
SQL_CONFIG = CONFIG.get("sql", {})

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
REST_PROCESSED_ORDERS_PATH = PROCESSED_DIR / "rest_api_processed_orders.json"
SQL_PROCESSED_ORDERS_PATH = PROCESSED_DIR / "sql_processed_orders.json"
ERRORS_DIR = resolve_package_path(
    RUNTIME_CONFIG.get("errors_dir", "runtime/errors")
)
PROFILES_DIR = resolve_package_path(
    RUNTIME_CONFIG.get("profiles_dir", "runtime/profiles")
)
REST_IMPORT_MAPPING_PATH = PROFILES_DIR / "rest_api_import_mapping.json"
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
REST_API_ENABLED = bool(REST_API_CONFIG.get("enabled", False))
REST_API_IMPORT_ENABLED = bool(REST_API_CONFIG.get("import_enabled", False))
REST_API_EXPORT_ENABLED = bool(REST_API_CONFIG.get("export_enabled", False))
REST_API_POLL_INTERVAL = int(REST_API_CONFIG.get("poll_interval_seconds", 60))
SQL_ENABLED = bool(SQL_CONFIG.get("enabled", False))
SQL_IMPORT_ENABLED = bool(SQL_CONFIG.get("import_enabled", False))
SQL_EXPORT_ENABLED = bool(SQL_CONFIG.get("export_enabled", False))
SQL_POLL_INTERVAL = int(SQL_CONFIG.get("poll_interval_seconds", 60))


try:
    from src.pipeline.file_processing_pipeline import FileProcessingPipeline
except ImportError as error:
    log.error(f"Could not import FileProcessingPipeline: {error}")
    log.error("This portable package must include src/ and agents/ folders.")
    sys.exit(1)

try:
    from src.connectors.rest_api_connector import RestApiConnector, clean_json_response
    from src.ai.openai_client import OpenAIClient
except ImportError as error:
    # Keep REST optional. File-based middleware still works when REST is disabled.
    RestApiConnector = None
    OpenAIClient = None
    clean_json_response = None
    log.warning(f"REST API connector unavailable: {error}")

try:
    from src.connectors.db_connector import DBConnector
except ImportError as error:
    # Keep SQL optional. File-based and REST middleware still work when SQL is disabled.
    DBConnector = None
    log.warning(f"DBConnector unavailable: {error}")


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
    # Modula export files are XML. Ignore our own IMP_ORDINI files by name so
    # the runtime does not repeatedly open old import XML files in the shared
    # IMPEXP folder. EXP_ORDINI content is still validated before processing.
    if not file_path.is_file():
        return False

    if file_path.suffix.lower() != ".xml":
        return False

    name = file_path.name.upper()

    if name.startswith("IMP_ORDINI"):
        return False

    return "EXP_ORDINI" in name or name.startswith("EXP")


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
    # Convert parsed EXP_ORDINI data back into the customer's original format.
    #
    # The profile is created during import and records the source_type that was
    # actually received from the customer. This prevents XML imports from being
    # exported as CSV just because config.json has customer_output.format = csv.
    profile = load_customer_profile()
    field_mapping = get_profile_field_mapping(profile)

    output_format = (
        profile.get("source_type")
        or CUSTOMER_OUTPUT_FORMAT
    ).lower()

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



def get_nested_value(source: dict, dotted_key: str, default: object = "") -> object:
    # Supports simple field names and dotted API paths like customer.name.
    if not dotted_key:
        return default

    current = source

    for part in str(dotted_key).split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default

    return current


def extract_records_from_api_data(api_data: object, records_key: str | None) -> list[dict]:
    # Normalize common REST responses into a list of records.
    # Supports a raw list, {"orders": [...]}, or a dotted records_key path.
    records = api_data

    if records_key and isinstance(api_data, dict):
        records = get_nested_value(api_data, records_key, default=[])
    elif isinstance(api_data, dict):
        records = api_data.get("orders", api_data.get("data", []))

    if isinstance(records, dict):
        records = records.get("orders", records.get("data", [records]))

    if not isinstance(records, list):
        return []

    return [record for record in records if isinstance(record, dict)]


def get_rest_source_fields(records: list[dict]) -> list[str]:
    # Collect every available source field from representative REST records.
    # Exact field spelling is preserved so OpenAI can return a usable mapping.
    fields = set()

    for record in records[:20]:
        if not isinstance(record, dict):
            continue

        for key in record.keys():
            fields.add(str(key))

    return sorted(fields)


def validate_rest_mapping(mapping: dict, records: list[dict]) -> dict:
    # Require the four canonical fields and verify that OpenAI selected fields
    # that actually exist in the REST response.
    required_fields = ["order_id", "customer_name", "item", "quantity"]

    if not isinstance(mapping, dict):
        raise ValueError("REST field mapping must be a JSON object.")

    cleaned_mapping = {
        field: str(mapping.get(field, "")).strip()
        for field in required_fields
    }

    missing = [
        field
        for field, source_field in cleaned_mapping.items()
        if not source_field
    ]

    if missing:
        raise ValueError(
            "REST field mapping is missing required canonical fields: "
            + ", ".join(missing)
        )

    source_fields = set(get_rest_source_fields(records))
    invalid = [
        source_field
        for source_field in cleaned_mapping.values()
        if source_field.split(".")[0] not in source_fields
    ]

    if invalid:
        raise ValueError(
            "REST field mapping contains fields not found in the API response: "
            + ", ".join(invalid)
        )

    return cleaned_mapping


def load_saved_rest_mapping() -> dict:
    # REST import mappings are kept separate from customer export profiles.
    if not REST_IMPORT_MAPPING_PATH.exists():
        return {}

    try:
        with open(REST_IMPORT_MAPPING_PATH, "r", encoding="utf-8") as file:
            payload = json.load(file)

        mapping = payload.get("field_mapping", payload)

        if isinstance(mapping, dict):
            return mapping

    except Exception as error:
        log.warning(f"Could not load saved REST import mapping: {error}")

    return {}


def save_rest_mapping(mapping: dict, records: list[dict]) -> Path:
    REST_IMPORT_MAPPING_PATH.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "source_type": "rest_api",
        "customer_name": CONFIG.get("customer_name", ""),
        "field_mapping": mapping,
        "source_fields": get_rest_source_fields(records),
        "created_at": datetime.now().isoformat(),
    }

    with open(REST_IMPORT_MAPPING_PATH, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=4)

    return REST_IMPORT_MAPPING_PATH


def infer_rest_mapping_with_openai(records: list[dict]) -> dict:
    # Ask OpenAI to understand unfamiliar REST response fields instead of
    # requiring the customer to manually configure a parser mapping.
    if OpenAIClient is None or clean_json_response is None:
        raise ImportError(
            "OpenAI REST mapping is unavailable because the AI client "
            "or response cleaner could not be imported."
        )

    if not records:
        raise ValueError("Cannot infer REST mapping from an empty API response.")

    source_fields = get_rest_source_fields(records)
    sample_records = records[:10]

    prompt = f'''
You are a warehouse and Modula WMS data-integration specialist.

Analyze the REST API source fields and sample records below. Identify the exact
source field that maps to each canonical order field:

- order_id: purchase order number, order number, PO number, transaction number
- customer_name: customer, company, buyer, client, account, organization
- item: part number, SKU, article, product code, material number
- quantity: requested quantity, ordered quantity, required quantity, units

Return ONLY valid JSON in exactly this shape:

{{
    "order_id": "exact source field",
    "customer_name": "exact source field",
    "item": "exact source field",
    "quantity": "exact source field"
}}

Rules:
- Preserve the exact source field spelling and capitalization.
- Do not invent fields.
- Use dotted paths only when the value is nested.
- Do not include markdown or explanation.

Available source fields:
{json.dumps(source_fields, indent=2)}

Sample REST records:
{json.dumps(sample_records, indent=2, default=str)}
'''

    response_text = OpenAIClient().ask(prompt)
    cleaned_response = clean_json_response(response_text)

    try:
        mapping = json.loads(cleaned_response)
    except json.JSONDecodeError as error:
        raise ValueError(
            "OpenAI returned invalid JSON while mapping REST fields. "
            f"Response preview: {response_text[:500]}"
        ) from error

    return validate_rest_mapping(mapping, records)


def rest_field_mapping(records: list[dict]) -> dict:
    # Mapping priority:
    # 1. Explicit config.json override
    # 2. Saved REST-specific AI mapping
    # 3. OpenAI analysis of the live REST response
    configured_mapping = REST_API_CONFIG.get("field_mapping", {})

    if isinstance(configured_mapping, dict) and configured_mapping:
        mapping = validate_rest_mapping(configured_mapping, records)
        log.info(f"Using configured REST field mapping: {mapping}")
        return mapping

    saved_mapping = load_saved_rest_mapping()

    if saved_mapping:
        try:
            mapping = validate_rest_mapping(saved_mapping, records)
            log.info(
                f"Loaded saved REST AI mapping: "
                f"{REST_IMPORT_MAPPING_PATH.name} -> {mapping}"
            )
            return mapping
        except Exception as error:
            log.warning(
                "Saved REST mapping no longer matches the API response; "
                f"requesting a new AI mapping. Reason: {error}"
            )

    log.info(
        "No usable REST mapping found. Asking OpenAI to analyze "
        "the live API response."
    )
    mapping = infer_rest_mapping_with_openai(records)
    mapping_path = save_rest_mapping(mapping, records)
    log.info(f"OpenAI REST mapping identified: {mapping}")
    log.info(f"Saved REST import mapping: {mapping_path}")
    return mapping


def normalize_rest_records_to_orders(records: list[dict], field_mapping: dict) -> list[dict]:
    # Convert API records into the same flat JSON order rows that the existing
    # JsonOrderParser already understands. This lets REST import reuse the
    # proven file pipeline instead of creating a separate conversion path.
    normalized_rows = []

    for record in records:
        if field_mapping:
            normalized_rows.append(
                {
                    "order_id": get_nested_value(record, field_mapping.get("order_id", "order_id")),
                    "customer_name": get_nested_value(record, field_mapping.get("customer_name", "customer_name")),
                    "item": get_nested_value(record, field_mapping.get("item", "item")),
                    "quantity": get_nested_value(record, field_mapping.get("quantity", "quantity")),
                }
            )
        else:
            # If the API already returns canonical fields, keep it as-is.
            normalized_rows.append(record)

    return [row for row in normalized_rows if row.get("order_id") and row.get("item")]


def load_processed_rest_order_ids() -> set[str]:
    # Persistent REST import memory.
    #
    # REST APIs usually keep returning the same available orders until the
    # customer system marks them complete. This local state prevents the runtime
    # from generating a new IMP_ORDINI file for the same order_id every time it
    # polls the import URL.
    if not REST_PROCESSED_ORDERS_PATH.exists():
        return set()

    try:
        with open(REST_PROCESSED_ORDERS_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return {str(order_id) for order_id in data if str(order_id).strip()}

    except Exception as error:
        log.warning(f"Could not load REST processed order IDs: {error}")

    return set()


def save_processed_rest_order_ids(order_ids: set[str]) -> None:
    # Save REST import memory without touching any other runtime state.
    REST_PROCESSED_ORDERS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(REST_PROCESSED_ORDERS_PATH, "w", encoding="utf-8") as file:
        json.dump(sorted(order_ids), file, indent=4)


def filter_new_rest_order_rows(normalized_rows: list[dict]) -> tuple[list[dict], set[str]]:
    # Keep only rows whose order_id has not been processed before.
    #
    # If an order has multiple line rows, all rows for that order_id are kept
    # together the first time the order is seen. Later polls skip that order_id.
    processed_order_ids = load_processed_rest_order_ids()
    new_rows = []
    new_order_ids = set()

    for row in normalized_rows:
        order_id = str(row.get("order_id", "")).strip()

        if not order_id:
            continue

        if order_id in processed_order_ids:
            continue

        new_rows.append(row)
        new_order_ids.add(order_id)

    return new_rows, new_order_ids


def mark_rest_orders_processed(order_ids: set[str]) -> None:
    # Mark orders as processed only after the existing pipeline reports success.
    if not order_ids:
        return

    processed_order_ids = load_processed_rest_order_ids()
    processed_order_ids.update(order_ids)
    save_processed_rest_order_ids(processed_order_ids)


def write_rest_import_temp_file(api_data: object) -> tuple[Path, set[str]]:
    # Store only new API orders as a temporary customer JSON file. The existing
    # FileProcessingPipeline will parse it, generate IMP_ORDINI XML, move it to
    # processed/, and copy the XML to the Modula IMPEXP folder.
    records_key = REST_API_CONFIG.get("records_key", "orders")
    records = extract_records_from_api_data(api_data, records_key)
    if not records:
        raise ValueError("REST API response contained no record objects.")

    mapping = rest_field_mapping(records)
    normalized_rows = normalize_rest_records_to_orders(records, mapping)

    if not normalized_rows:
        raise ValueError("REST API import returned no usable order rows.")

    new_rows, new_order_ids = filter_new_rest_order_rows(normalized_rows)

    if not new_rows:
        log.info("REST import found no new orders. Already processed order IDs are being skipped.")
        return None, set()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_path = INPUT_DIR / f"rest_api_import_{timestamp}.json"

    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump({"orders": new_rows}, file, indent=4)

    return temp_path, new_order_ids


def process_rest_api_import(pipeline: FileProcessingPipeline) -> None:
    # Poll the configured REST endpoint for new customer orders.
    # Disabled by default; turn on rest_api.enabled and rest_api.import_enabled
    # in config.json for customer API integrations.
    if not (REST_API_ENABLED and REST_API_IMPORT_ENABLED):
        return

    if RestApiConnector is None:
        log.error("REST import is enabled but RestApiConnector could not be imported.")
        return

    import_url = REST_API_CONFIG.get("import_url", "")

    if not import_url:
        log.warning("REST import is enabled but rest_api.import_url is blank.")
        return

    connector = RestApiConnector()
    result = connector.get_json(
        url=import_url,
        headers=REST_API_CONFIG.get("headers", {}),
        params=REST_API_CONFIG.get("params", {}),
        api_key=REST_API_CONFIG.get("api_key") or None,
        api_key_header=REST_API_CONFIG.get("api_key_header", "Authorization"),
        bearer_token=bool(REST_API_CONFIG.get("bearer_token", True)),
        timeout=int(REST_API_CONFIG.get("timeout_seconds", 30)),
        max_retries=int(REST_API_CONFIG.get("max_retries", 3)),
    )

    if result.get("status") != "success":
        log.error(f"REST IMPORT FAILED: {result.get('error') or result.get('message')}")
        return

    try:
        temp_file, new_order_ids = write_rest_import_temp_file(result.get("data"))

        if temp_file is None:
            return

        log.info(f"REST import saved temporary customer JSON: {temp_file.name}")
        processing_result = process_customer_input_file(pipeline, temp_file)

        if processing_result and processing_result.get("status") == "success":
            mark_rest_orders_processed(new_order_ids)
            log.info(f"REST import marked processed order IDs: {sorted(new_order_ids)}")
        else:
            log.warning(
                "REST import was not marked processed because the file pipeline "
                "did not return success."
            )

    except Exception as error:
        log.error(f"REST import processing failed: {error}")




def get_sql_connection_string() -> str:
    # SQLite database paths are package-relative by default. ODBC connection
    # strings are passed through exactly as entered by the customer.
    connection_string = SQL_CONFIG.get("connection_string", "")
    database_type = str(SQL_CONFIG.get("database_type", "sqlite")).lower()

    if database_type == "sqlite" and connection_string:
        return str(resolve_package_path(connection_string))

    return connection_string


def sql_field_mapping() -> dict:
    # SQL imports can use an explicit mapping in config.json. If none is set,
    # fall back to the saved customer profile from the file onboarding flow.
    configured_mapping = SQL_CONFIG.get("field_mapping", {})

    if isinstance(configured_mapping, dict) and configured_mapping:
        return configured_mapping

    profile = load_customer_profile()
    return get_profile_field_mapping(profile)


def normalize_sql_records_to_orders(records: list[dict], field_mapping: dict) -> list[dict]:
    # Convert SQL rows into the same flat JSON order rows that the existing
    # JsonOrderParser already understands. This lets SQL import reuse the
    # proven file pipeline instead of creating a separate conversion path.
    normalized_rows = []

    for record in records:
        if field_mapping:
            normalized_rows.append(
                {
                    "order_id": get_nested_value(record, field_mapping.get("order_id", "order_id")),
                    "customer_name": get_nested_value(record, field_mapping.get("customer_name", "customer_name")),
                    "item": get_nested_value(record, field_mapping.get("item", "item")),
                    "quantity": get_nested_value(record, field_mapping.get("quantity", "quantity")),
                }
            )
        else:
            # If the SQL query already aliases columns to canonical fields,
            # keep the row as-is.
            normalized_rows.append(record)

    return [row for row in normalized_rows if row.get("order_id") and row.get("item")]


def load_processed_sql_order_ids() -> set[str]:
    # Persistent SQL import memory.
    # This prevents the runtime from repeatedly importing the same database
    # order rows every time it polls the SELECT query.
    if not SQL_PROCESSED_ORDERS_PATH.exists():
        return set()

    try:
        with open(SQL_PROCESSED_ORDERS_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return {str(order_id) for order_id in data if str(order_id).strip()}

    except Exception as error:
        log.warning(f"Could not load SQL processed order IDs: {error}")

    return set()


def save_processed_sql_order_ids(order_ids: set[str]) -> None:
    # Save SQL import memory without touching any other runtime state.
    SQL_PROCESSED_ORDERS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(SQL_PROCESSED_ORDERS_PATH, "w", encoding="utf-8") as file:
        json.dump(sorted(order_ids), file, indent=4)


def filter_new_sql_order_rows(normalized_rows: list[dict]) -> tuple[list[dict], set[str]]:
    # Keep only rows whose order_id has not been processed before.
    # If an order has multiple line rows, all rows for that order_id are kept
    # together the first time the order is seen. Later polls skip that order_id.
    processed_order_ids = load_processed_sql_order_ids()
    new_rows = []
    new_order_ids = set()

    for row in normalized_rows:
        order_id = str(row.get("order_id", "")).strip()

        if not order_id:
            continue

        if order_id in processed_order_ids:
            continue

        new_rows.append(row)
        new_order_ids.add(order_id)

    return new_rows, new_order_ids


def mark_sql_orders_processed(order_ids: set[str]) -> None:
    # Mark SQL orders as processed only after the existing pipeline succeeds.
    if not order_ids:
        return

    processed_order_ids = load_processed_sql_order_ids()
    processed_order_ids.update(order_ids)
    save_processed_sql_order_ids(processed_order_ids)


def fetch_sql_import_rows() -> list[dict]:
    # Execute the configured SQL import query and return rows as dictionaries.
    if DBConnector is None:
        raise ImportError("SQL import is enabled but DBConnector could not be imported.")

    connection_string = get_sql_connection_string()
    database_type = str(SQL_CONFIG.get("database_type", "sqlite")).lower()
    import_query = SQL_CONFIG.get("import_query", "")

    if not connection_string:
        raise ValueError("SQL import is enabled but sql.connection_string is blank.")

    if not import_query:
        raise ValueError("SQL import is enabled but sql.import_query is blank.")

    with DBConnector(
        connection_string=connection_string,
        database_type=database_type,
    ) as database:
        return database.fetch_all(import_query)


def write_sql_import_temp_file(rows: list[dict]) -> tuple[Path | None, set[str]]:
    # Store only new SQL orders as a temporary customer JSON file. The existing
    # FileProcessingPipeline will parse it, generate IMP_ORDINI XML, move it to
    # processed/, and copy the XML to the Modula IMPEXP folder.
    mapping = sql_field_mapping()
    normalized_rows = normalize_sql_records_to_orders(rows, mapping)

    if not normalized_rows:
        raise ValueError("SQL import query returned no usable order rows.")

    new_rows, new_order_ids = filter_new_sql_order_rows(normalized_rows)

    if not new_rows:
        log.info("SQL import found no new orders. Already processed order IDs are being skipped.")
        return None, set()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_path = INPUT_DIR / f"sql_import_{timestamp}.json"

    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump({"orders": new_rows}, file, indent=4)

    return temp_path, new_order_ids


def process_sql_import(pipeline: FileProcessingPipeline) -> None:
    # Poll the configured database for new customer orders.
    # Disabled by default; turn on sql.enabled and sql.import_enabled in
    # config.json or through setup_database.bat for SQL/ODBC integrations.
    if not (SQL_ENABLED and SQL_IMPORT_ENABLED):
        return

    try:
        rows = fetch_sql_import_rows()
        temp_file, new_order_ids = write_sql_import_temp_file(rows)

        if temp_file is None:
            return

        log.info(f"SQL import saved temporary customer JSON: {temp_file.name}")
        processing_result = process_customer_input_file(pipeline, temp_file)

        if processing_result and processing_result.get("status") == "success":
            mark_sql_orders_processed(new_order_ids)
            log.info(f"SQL import marked processed order IDs: {sorted(new_order_ids)}")
        else:
            log.warning(
                "SQL import was not marked processed because the file pipeline "
                "did not return success."
            )

    except Exception as error:
        log.error(f"SQL import processing failed: {error}")


def safe_sql_identifier(identifier: str) -> str:
    # Keep SQL table/column identifiers conservative because they come from
    # config.json. This prevents accidental malformed INSERT statements while
    # still supporting common names like dbo.order_confirmations.
    cleaned = str(identifier or "").strip()

    if not cleaned:
        raise ValueError("SQL identifier cannot be blank.")

    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.$[]")

    if any(character not in allowed for character in cleaned):
        raise ValueError(f"Unsafe SQL identifier: {identifier}")

    return cleaned


def build_sql_export_rows(export_orders: list[dict]) -> list[dict]:
    # Build stable SQL confirmation rows from Modula EXP_ORDINI data.
    #
    # Unlike customer CSV/XML/JSON output, SQL export uses canonical database
    # columns by default. That makes inserts predictable for tables such as:
    # order_id, item, quantity, operation_type, exported_at.
    timestamp = datetime.now().isoformat()
    rows = []

    for order in export_orders:
        for line in order.get("lines", []):
            row = {
                "order_id": order.get("order_id", ""),
                "customer_name": order.get("customer_name", ""),
                "item": line.get("item", ""),
                "quantity": line.get("quantity", ""),
                "operation_type": order.get("operation_type", ""),
                "warehouse_number": order.get("warehouse_number", ""),
                "bay_number": order.get("bay_number", ""),
                "sub1": line.get("sub1", ""),
                "warehouse_task": line.get("warehouse_task", ""),
                "source_bin": line.get("source_bin", ""),
                "destination_bin": line.get("destination_bin", ""),
                "exported_at": timestamp,
            }

            rows.append(row)

    if not rows:
        return []

    fieldnames = list(rows[0].keys())
    fields_with_any_value = [
        field
        for field in fieldnames
        if any(not is_blank_export_value(row.get(field)) for row in rows)
    ]

    cleaned_rows = []

    for row in rows:
        cleaned_rows.append(
            {
                field: row.get(field, "")
                for field in fields_with_any_value
                if not is_blank_export_value(row.get(field))
            }
        )

    return cleaned_rows


def insert_sql_export_rows(rows: list[dict]) -> int:
    # Insert Modula confirmation rows into the configured SQL export table.
    if DBConnector is None:
        raise ImportError("SQL export is enabled but DBConnector could not be imported.")

    if not rows:
        return 0

    connection_string = get_sql_connection_string()
    database_type = str(SQL_CONFIG.get("database_type", "sqlite")).lower()
    export_table = safe_sql_identifier(SQL_CONFIG.get("export_table", ""))

    if not connection_string:
        raise ValueError("SQL export is enabled but sql.connection_string is blank.")

    # Use the first row's keys to define the insert columns. The rows were
    # already normalized so every row shares the same useful columns.
    columns = [safe_sql_identifier(column) for column in rows[0].keys()]
    placeholders = ", ".join(["?"] * len(columns))
    column_sql = ", ".join(columns)
    insert_sql = f"INSERT INTO {export_table} ({column_sql}) VALUES ({placeholders})"

    inserted_count = 0

    with DBConnector(
        connection_string=connection_string,
        database_type=database_type,
    ) as database:
        for row in rows:
            params = [row.get(column, "") for column in rows[0].keys()]
            database.execute(insert_sql, params)
            inserted_count += 1

    return inserted_count


def process_sql_export(export_orders: list[dict]) -> None:
    # Insert Modula EXP_ORDINI confirmations back into the configured database.
    # This runs in addition to local customer_output files and REST export, so
    # existing export behavior remains unchanged.
    if not (SQL_ENABLED and SQL_EXPORT_ENABLED):
        return

    try:
        rows = build_sql_export_rows(export_orders)

        if not rows:
            log.info("SQL export found no rows to insert.")
            return

        inserted_count = insert_sql_export_rows(rows)
        log.info(
            f"SQL EXPORT SUCCESS inserted_rows={inserted_count} "
            f"table={SQL_CONFIG.get('export_table')}"
        )

    except Exception as error:
        log.error(f"SQL export failed: {error}")


def build_rest_export_payload(export_orders: list[dict], field_mapping: dict) -> dict:
    # Build the same cleaned, customer-shaped JSON payload used by file exports.
    customer_rows = map_export_rows_to_customer_fields(export_orders, field_mapping)

    return {
        "source_system": "Modula WMS",
        "document_type": "EXP_ORDINI",
        "exported_at": datetime.now().isoformat(),
        "orders": group_customer_rows_for_json(customer_rows, field_mapping),
    }


def post_rest_api_export(export_orders: list[dict]) -> None:
    # Send Modula EXP_ORDINI confirmations to a customer REST endpoint.
    # This runs in addition to writing the local customer_output file, preserving
    # the existing export behavior while adding API delivery.
    if not (REST_API_ENABLED and REST_API_EXPORT_ENABLED):
        return

    if RestApiConnector is None:
        log.error("REST export is enabled but RestApiConnector could not be imported.")
        return

    export_url = REST_API_CONFIG.get("export_url", "")

    if not export_url:
        log.warning("REST export is enabled but rest_api.export_url is blank.")
        return

    profile = load_customer_profile()
    field_mapping = get_profile_field_mapping(profile)
    payload = build_rest_export_payload(export_orders, field_mapping)
    connector = RestApiConnector()
    method = REST_API_CONFIG.get("export_method", "POST").upper()

    if method == "PUT":
        result = connector.put_json(
            url=export_url,
            json_body=payload,
            headers=REST_API_CONFIG.get("headers", {}),
            params=REST_API_CONFIG.get("params", {}),
            api_key=REST_API_CONFIG.get("api_key") or None,
            api_key_header=REST_API_CONFIG.get("api_key_header", "Authorization"),
            bearer_token=bool(REST_API_CONFIG.get("bearer_token", True)),
            timeout=int(REST_API_CONFIG.get("timeout_seconds", 30)),
            max_retries=int(REST_API_CONFIG.get("max_retries", 3)),
        )
    else:
        result = connector.post_json(
            url=export_url,
            json_body=payload,
            headers=REST_API_CONFIG.get("headers", {}),
            params=REST_API_CONFIG.get("params", {}),
            api_key=REST_API_CONFIG.get("api_key") or None,
            api_key_header=REST_API_CONFIG.get("api_key_header", "Authorization"),
            bearer_token=bool(REST_API_CONFIG.get("bearer_token", True)),
            timeout=int(REST_API_CONFIG.get("timeout_seconds", 30)),
            max_retries=int(REST_API_CONFIG.get("max_retries", 3)),
        )

    if result.get("status") == "success":
        log.info(f"REST EXPORT SUCCESS status_code={result.get('status_code')} url={export_url}")
    else:
        log.error(f"REST EXPORT FAILED: {result.get('error') or result.get('message')}")


def process_customer_input_file(pipeline: FileProcessingPipeline, file_path: Path) -> dict:
    # Process customer-originated order files into Modula IMP_ORDINI XML.
    # Returning the pipeline result lets REST import mark order IDs as processed
    # only after the existing file pipeline succeeds.
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

    return result


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
    post_rest_api_export(export_orders)
    process_sql_export(export_orders)
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
    log.info("  FinalACT4 AI Middleware Runtime")
    log.info("=" * 60)
    log.info(f"  Generator version: {CONFIG.get('generator_version', 'unknown')}")
    log.info(f"  Package schema   : {CONFIG.get('package_schema_version', 'unknown')}")
    log.info(f"  Package          : {PACKAGE_DIR}")
    log.info(f"  Customer input   : {INPUT_DIR}")
    log.info(f"  Modula XML out   : {MODULA_OUT_DIR}")
    log.info(f"  WMS IMPEXP       : {WMS_ORDER_IMPORT_DIR}")
    log.info(f"  WMS export watch : {WMS_EXPORT_WATCH_DIR}")
    log.info(f"  Customer output  : {CUSTOMER_OUTPUT_DIR}")
    log.info(f"  Output format    : {CUSTOMER_OUTPUT_FORMAT}")
    log.info(f"  REST enabled     : {REST_API_ENABLED}")
    log.info(f"  REST import      : {REST_API_IMPORT_ENABLED}")
    log.info(f"  REST export      : {REST_API_EXPORT_ENABLED}")
    log.info(f"  SQL enabled      : {SQL_ENABLED}")
    log.info(f"  SQL import       : {SQL_IMPORT_ENABLED}")
    log.info(f"  SQL export       : {SQL_EXPORT_ENABLED}")
    enabled_integrations = ["Files"]
    if REST_API_ENABLED:
        enabled_integrations.append("REST API")
    if SQL_ENABLED:
        enabled_integrations.append("SQL/ODBC")
    log.info(f"  Active flows     : {', '.join(enabled_integrations)}")
    log.info(f"  Processed        : {PROCESSED_DIR}")
    log.info(f"  Errors           : {ERRORS_DIR}")
    log.info(f"  Profiles         : {PROFILES_DIR}")
    log.info(f"  Supported input  : {', '.join(SUPPORTED_EXTENSIONS)}")
    log.info("  Drop CSV/JSON/XML customer files into customer_input.")
    log.info("  Drop or wait for Modula EXP_ORDINI XML files in the WMS IMPEXP folder.")
    log.info("=" * 60)

    seen_customer_inputs = set()
    seen_wms_exports = set()
    last_rest_import_poll = 0.0
    last_sql_import_poll = 0.0

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

            if REST_API_ENABLED and REST_API_IMPORT_ENABLED:
                now = time.time()
                if now - last_rest_import_poll >= REST_API_POLL_INTERVAL:
                    last_rest_import_poll = now
                    process_rest_api_import(pipeline)

            if SQL_ENABLED and SQL_IMPORT_ENABLED:
                now = time.time()
                if now - last_sql_import_poll >= SQL_POLL_INTERVAL:
                    last_sql_import_poll = now
                    process_sql_import(pipeline)

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
            log.info("Shutdown requested — stopping middleware cleanly.")
            break

        except Exception as error:
            log.error(f"Watcher error: {error}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
