"""
generate_test_package.py

Run from project root:
    python generate_test_package.py
    python generate_test_package.py Ford
    python generate_test_package.py "Acme Manufacturing"

Creates a portable customer runtime package:

    generated_integrations/
    └── <customer_name>/
        ├── start.bat
        ├── setup_api.bat
        ├── setup_rest_api.py
        ├── setup_database.bat
        ├── setup_sql_odbc.py
        ├── always_on_runtime.py
        ├── config.json
        ├── README.md
        ├── agents/
        ├── src/
        └── runtime/
            ├── customer_input/        <- drop customer CSV, JSON, or XML files here
            ├── customer_output/
            ├── modula_output/         <- generated XML appears here
            ├── processed/
            ├── errors/
            ├── profiles/
            ├── sql/                 <- SQLite test database folder
            └── wms_order_import_test/ <- default test WMS import path
"""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path


DEFAULT_CUSTOMER_NAME = "ESA_Test"
DEFAULT_SOURCE_TYPE = "csv"
TARGET_SYSTEM = "Modula WMS"
TARGET_FORMAT = "XML"
DEFAULT_WMS_ORDER_IMPORT_PATH = r"C:\SystemLogistics\IMPEXP"
SUPPORTED_SOURCE_TYPES = ["csv", "json", "xml"]
SUPPORTED_FILE_EXTENSIONS = [".csv", ".json", ".xml"]
GENERATOR_VERSION = "1.5.0"
PACKAGE_SCHEMA_VERSION = "1.5.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a portable Modula WMS AI middleware runtime package."
    )
    parser.add_argument(
        "customer_name",
        nargs="?",
        default=DEFAULT_CUSTOMER_NAME,
        help=f"Customer name. Default: {DEFAULT_CUSTOMER_NAME}",
    )
    parser.add_argument(
        "--source-type",
        default=DEFAULT_SOURCE_TYPE,
        choices=SUPPORTED_SOURCE_TYPES,
        help=(
            "Primary customer source type for documentation/config purposes. "
            f"Supported: {', '.join(SUPPORTED_SOURCE_TYPES)}. "
            f"Default: {DEFAULT_SOURCE_TYPE}"
        ),
    )
    parser.add_argument(
        "--wms-order-import-path",
        default=DEFAULT_WMS_ORDER_IMPORT_PATH,
        help=(
            "WMS order import path. Can be relative to the package folder "
            "or an absolute Windows path."
        ),
    )
    return parser.parse_args()


def safe_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        file.write(content)


def copy_folder(source: Path, destination: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Missing required folder: {source}")

    if destination.exists():
        shutil.rmtree(destination)

    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(
            "__pycache__",
            "*.pyc",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".venv",
            "venv",
            ".git",
        ),
    )


def validate_runtime_engine_files() -> None:
    """
    Confirms the generator is packaging the runtime code needed for CSV/JSON/XML.

    The generator copies the live src/ and agents/ folders into each generated
    package, so these files need to exist before creating a package. This check
    catches missing parser/pipeline files early instead of creating a broken
    portable package.
    """

    required_paths = [
        Path("src") / "pipeline" / "file_processing_pipeline.py",
        Path("src") / "converters" / "csv_to_canonical.py",
        Path("src") / "formatters" / "modula_ordini_xml_formatter.py",
        Path("src") / "ai" / "header_extraction_agent.py",
        Path("src") / "connectors" / "rest_api_connector.py",
        Path("src") / "connectors" / "db_connector.py",
        Path("agents") / "openai_field_mapping_agent.py",
    ]

    # Parser files live in parsing/ in this project.
    # We allow both src/parsing/ and a top-level parsing/ folder so the generator
    # works with the current project layout and any package layout copied forward.
    json_parser_candidates = [
        Path("src") / "parsing" / "json_order_parser.py",
        Path("parsing") / "json_order_parser.py",
        Path("json_order_parser.py"),
    ]
    xml_parser_candidates = [
        Path("src") / "parsing" / "xml_order_parser.py",
        Path("parsing") / "xml_order_parser.py",
        Path("xml_order_parser.py"),
    ]

    missing = [str(path) for path in required_paths if not path.exists()]

    if not any(path.exists() for path in json_parser_candidates):
        missing.append("json_order_parser.py in src/parsing/, parsing/, or project root")

    if not any(path.exists() for path in xml_parser_candidates):
        missing.append("xml_order_parser.py in src/parsing/, parsing/, or project root")

    if missing:
        raise FileNotFoundError(
            "Cannot generate package because required runtime files are missing:\n"
            + "\n".join(f"  - {item}" for item in missing)
        )


def create_runtime_folders(base: Path) -> None:
    folders = [
        base / "runtime" / "customer_input",
        base / "runtime" / "customer_output",
        base / "runtime" / "modula_output",
        base / "runtime" / "processed",
        base / "runtime" / "errors",
        base / "runtime" / "profiles",
        base / "runtime" / "sql",
        base / "runtime" / "wms_order_import_test",
        base / "runtime" / "wms_export_processed",
    ]
    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)
    print("  [OK] Runtime folders created")


def copy_runtime_engine(base: Path) -> None:
    """
    Copies the current runtime engine into the generated customer package.

    Important: JSON/XML behavior comes from the pipeline and parser files copied
    here. After changing src/pipeline/file_processing_pipeline.py or parser files,
    regenerate the package so the customer package receives the new behavior.
    """

    copy_folder(Path("src"), base / "src")
    copy_folder(Path("agents"), base / "agents")

    # If parser files are still in a top-level parsing/ folder, copy that too.
    # This prevents generated packages from breaking when parser modules live
    # outside src/.
    if Path("parsing").exists():
        copy_folder(Path("parsing"), base / "parsing")

    print("  [OK] Runtime engine copied")


def create_config(
    base: Path,
    customer_name: str,
    source_type: str,
    wms_order_import_path: str,
) -> None:
    config = {
        "customer_name": customer_name,
        "source_type": source_type,
        "supported_source_types": SUPPORTED_SOURCE_TYPES,
        "supported_file_extensions": SUPPORTED_FILE_EXTENSIONS,
        "target_system": TARGET_SYSTEM,
        "target_format": TARGET_FORMAT,
        "created_at": datetime.now().isoformat(),
        "generated_at": datetime.now().isoformat(),
        "generator_version": GENERATOR_VERSION,
        "package_schema_version": PACKAGE_SCHEMA_VERSION,
        "features": {
            "file_import_export": True,
            "csv": True,
            "json": True,
            "xml": True,
            "rest_api": True,
            "sql_odbc": True,
        },
        "runtime": {
            "input_dir": "runtime/customer_input",
            "output_dir": "runtime/customer_output",
            "modula_output_dir": "runtime/modula_output",
            "processed_dir": "runtime/processed",
            "errors_dir": "runtime/errors",
            "profiles_dir": "runtime/profiles",
            "wms_export_processed_dir": "runtime/wms_export_processed",
            "poll_interval_seconds": 5,
        },
        "wms": {
            # Modula uses the same IMPEXP folder for our generated IMP_ORDINI
            # files and for WMS-generated EXP_ORDINI files.
            "ordini_import_path": wms_order_import_path,
            "export_watch_path": wms_order_import_path,
        },
        "customer_output": {
            # The export side uses this format when converting Modula EXP_ORDINI
            # XML back to the customer's preferred format.
            # Supported values: csv, json, xml.
            "format": source_type,
        },
        "rest_api": {
            # REST API support is disabled by default so existing file-based
            # packages keep working exactly as before. Enable these settings
            # in config.json for customer API integrations.
            "enabled": False,
            "import_enabled": False,
            "export_enabled": False,
            "import_url": "",
            "export_url": "",
            "export_method": "POST",
            "headers": {},
            "params": {},
            "api_key": "",
            "api_key_header": "Authorization",
            "bearer_token": True,
            "records_key": "orders",
            "batch_key": "orders",
            "field_mapping": {},
            "poll_interval_seconds": 60,
            "timeout_seconds": 30,
            "max_retries": 3,
        },
        "sql": {
            # SQL / ODBC support is disabled by default so existing file and
            # REST packages continue to behave exactly as before. The setup
            # utility updates only this section when database integration is
            # needed.
            "enabled": False,
            "import_enabled": False,
            "export_enabled": False,
            "database_type": "sqlite",
            "connection_string": "runtime/sql/customer_orders.db",
            "import_query": "SELECT * FROM orders_to_modula",
            "export_table": "order_confirmations",
            "field_mapping": {},
            "processed_key_column": "order_id",
            "poll_interval_seconds": 60,
            "timeout_seconds": 30,
        },
    }
    write_json(base / "config.json", config)
    print("  [OK] config.json written")


def create_runtime_script(base: Path, customer_name: str) -> None:
    content = f"""\"\""
always_on_runtime.py — {customer_name} AI Middleware Runtime

Portable runtime package.

Import side:
- Watches runtime/customer_input for CSV, JSON, and XML customer order files.
- Converts customer order files into Modula IMP_ORDINI XML.
- Copies generated XML into the configured Modula IMPEXP folder.

Export side:
- Watches the configured Modula IMPEXP folder for EXP_ORDINI XML files.
- Converts Modula export order confirmations back into the customer's format.
- Writes customer-facing output files to runtime/customer_output.
\"\""

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
        raise FileNotFoundError(f"Missing config file: {{CONFIG_PATH}}")

    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def resolve_package_path(path_value: str) -> Path:
    path = Path(path_value)

    if path.is_absolute():
        return path

    return PACKAGE_DIR / path


CONFIG = load_config()
RUNTIME_CONFIG = CONFIG.get("runtime", {{}})
WMS_CONFIG = CONFIG.get("wms", {{}})
CUSTOMER_OUTPUT_CONFIG = CONFIG.get("customer_output", {{}})
REST_API_CONFIG = CONFIG.get("rest_api", {{}})
SQL_CONFIG = CONFIG.get("sql", {{}})

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
    log.error(f"Could not import FileProcessingPipeline: {{error}}")
    log.error("This portable package must include src/ and agents/ folders.")
    sys.exit(1)

try:
    from src.connectors.rest_api_connector import RestApiConnector
except ImportError as error:
    # Keep REST optional. File-based middleware still works when REST is disabled.
    RestApiConnector = None
    log.warning(f"REST API connector unavailable: {{error}}")

try:
    from src.connectors.db_connector import DBConnector
except ImportError as error:
    # Keep SQL optional. File-based and REST middleware still work when SQL is disabled.
    DBConnector = None
    log.warning(f"DBConnector unavailable: {{error}}")


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
        target_path = target_folder / f"{{source_path.stem}}_{{timestamp}}{{source_path.suffix}}"

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

        order = {{
            "order_id": order_number,
            "operation_type": clean_text(order_node.findtext("ORD_TIPOOP")),
            "warehouse_number": clean_text(order_node.findtext("ORD_ATTR1")),
            "bay_number": clean_text(order_node.findtext("ORD_ELEBAIE")),
            "lines": [],
        }}

        for line_node in order_node.findall(".//EXP_ORDINI_RIGHE"):
            order["lines"].append(
                {{
                    "order_id": clean_text(line_node.findtext("RIG_ORDINE")) or order_number,
                    "item": clean_text(line_node.findtext("RIG_ARTICOLO")),
                    "quantity": clean_text(line_node.findtext("RIG_QTAE")),
                    "sub1": clean_text(line_node.findtext("RIG_SUB1")),
                    "warehouse_task": clean_text(line_node.findtext("RIG_ATTR1")),
                    "source_bin": clean_text(line_node.findtext("RIG_ATTR2")),
                    "destination_bin": clean_text(line_node.findtext("RIG_ATTR3")),
                }}
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
        candidate_paths.append(PROFILES_DIR / f"{{safe_customer}}_profile.json")

    candidate_paths.extend(get_profile_files())

    for profile_path in candidate_paths:
        if not profile_path.exists():
            continue

        try:
            with open(profile_path, "r", encoding="utf-8") as file:
                profile = json.load(file)

            log.info(f"Loaded customer profile for export mapping: {{profile_path.name}}")
            return profile

        except Exception as error:
            log.warning(f"Could not load profile {{profile_path}}: {{error}}")

    log.warning(
        "No saved customer profile found. Export will use generic field names."
    )
    return {{}}


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
        or {{}}
    )

    if not isinstance(mapping, dict):
        return {{}}

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

    fallback_names = {{
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
    }}

    return fallback_names.get(internal_field, internal_field)


def flatten_export_orders(export_orders: list[dict]) -> list[dict]:
    # Flatten order/line data into the same canonical structure used by imports.
    rows = []

    for order in export_orders:
        for line in order.get("lines", []):
            rows.append(
                {{
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
                }}
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
        customer_row = {{
            customer_field_name(field_mapping, "order_id"): row.get("order_id", ""),
            customer_field_name(field_mapping, "customer_name"): row.get("customer_name", ""),
            customer_field_name(field_mapping, "item"): row.get("item", ""),
            customer_field_name(field_mapping, "quantity"): row.get("quantity", ""),
        }}

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
        cleaned_row = {{
            field: row.get(field, "")
            for field in fields_with_any_value
            if not is_blank_export_value(row.get(field))
        }}

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
    grouped_orders = {{}}

    for row in cleaned_rows:
        order_id = row.get(order_field, "")

        if not order_id:
            continue

        if order_id not in grouped_orders:
            grouped_order = {{
                order_field: order_id,
                "lines": [],
            }}

            if customer_field in row and not is_blank_export_value(row.get(customer_field)):
                grouped_order[customer_field] = row.get(customer_field, "")

            grouped_orders[order_id] = grouped_order

        line_payload = {{}}

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

    payload = {{
        "source_system": "Modula WMS",
        "document_type": "EXP_ORDINI",
        "exported_at": datetime.now().isoformat(),
        "orders": group_customer_rows_for_json(customer_rows, field_mapping),
    }}

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
        log.info(f"Using profile-driven export mapping: {{field_mapping}}")
    else:
        log.warning("Using generic export mapping because no field mapping was found.")

    if output_format not in ["json", "csv", "xml"]:
        log.warning(
            f"Unsupported customer output format '{{output_format}}'; defaulting to JSON."
        )
        output_format = "json"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = CUSTOMER_OUTPUT_DIR / f"{{source_file.stem}}_customer_export_{{timestamp}}.{{output_format}}"

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
    # Supports a raw list, {{"orders": [...]}}, or a dotted records_key path.
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


def rest_field_mapping() -> dict:
    # REST imports can use an explicit mapping in config.json. If none is set,
    # fall back to the saved customer profile from the file onboarding flow.
    configured_mapping = REST_API_CONFIG.get("field_mapping", {{}})

    if isinstance(configured_mapping, dict) and configured_mapping:
        return configured_mapping

    profile = load_customer_profile()
    return get_profile_field_mapping(profile)


def normalize_rest_records_to_orders(records: list[dict], field_mapping: dict) -> list[dict]:
    # Convert API records into the same flat JSON order rows that the existing
    # JsonOrderParser already understands. This lets REST import reuse the
    # proven file pipeline instead of creating a separate conversion path.
    normalized_rows = []

    for record in records:
        if field_mapping:
            normalized_rows.append(
                {{
                    "order_id": get_nested_value(record, field_mapping.get("order_id", "order_id")),
                    "customer_name": get_nested_value(record, field_mapping.get("customer_name", "customer_name")),
                    "item": get_nested_value(record, field_mapping.get("item", "item")),
                    "quantity": get_nested_value(record, field_mapping.get("quantity", "quantity")),
                }}
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
            return {{str(order_id) for order_id in data if str(order_id).strip()}}

    except Exception as error:
        log.warning(f"Could not load REST processed order IDs: {{error}}")

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
    mapping = rest_field_mapping()
    normalized_rows = normalize_rest_records_to_orders(records, mapping)

    if not normalized_rows:
        raise ValueError("REST API import returned no usable order rows.")

    new_rows, new_order_ids = filter_new_rest_order_rows(normalized_rows)

    if not new_rows:
        log.info("REST import found no new orders. Already processed order IDs are being skipped.")
        return None, set()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_path = INPUT_DIR / f"rest_api_import_{{timestamp}}.json"

    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump({{"orders": new_rows}}, file, indent=4)

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
        headers=REST_API_CONFIG.get("headers", {{}}),
        params=REST_API_CONFIG.get("params", {{}}),
        api_key=REST_API_CONFIG.get("api_key") or None,
        api_key_header=REST_API_CONFIG.get("api_key_header", "Authorization"),
        bearer_token=bool(REST_API_CONFIG.get("bearer_token", True)),
        timeout=int(REST_API_CONFIG.get("timeout_seconds", 30)),
        max_retries=int(REST_API_CONFIG.get("max_retries", 3)),
    )

    if result.get("status") != "success":
        log.error(f"REST IMPORT FAILED: {{result.get('error') or result.get('message')}}")
        return

    try:
        temp_file, new_order_ids = write_rest_import_temp_file(result.get("data"))

        if temp_file is None:
            return

        log.info(f"REST import saved temporary customer JSON: {{temp_file.name}}")
        processing_result = process_customer_input_file(pipeline, temp_file)

        if processing_result and processing_result.get("status") == "success":
            mark_rest_orders_processed(new_order_ids)
            log.info(f"REST import marked processed order IDs: {{sorted(new_order_ids)}}")
        else:
            log.warning(
                "REST import was not marked processed because the file pipeline "
                "did not return success."
            )

    except Exception as error:
        log.error(f"REST import processing failed: {{error}}")




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
    configured_mapping = SQL_CONFIG.get("field_mapping", {{}})

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
                {{
                    "order_id": get_nested_value(record, field_mapping.get("order_id", "order_id")),
                    "customer_name": get_nested_value(record, field_mapping.get("customer_name", "customer_name")),
                    "item": get_nested_value(record, field_mapping.get("item", "item")),
                    "quantity": get_nested_value(record, field_mapping.get("quantity", "quantity")),
                }}
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
            return {{str(order_id) for order_id in data if str(order_id).strip()}}

    except Exception as error:
        log.warning(f"Could not load SQL processed order IDs: {{error}}")

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
    temp_path = INPUT_DIR / f"sql_import_{{timestamp}}.json"

    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump({{"orders": new_rows}}, file, indent=4)

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

        log.info(f"SQL import saved temporary customer JSON: {{temp_file.name}}")
        processing_result = process_customer_input_file(pipeline, temp_file)

        if processing_result and processing_result.get("status") == "success":
            mark_sql_orders_processed(new_order_ids)
            log.info(f"SQL import marked processed order IDs: {{sorted(new_order_ids)}}")
        else:
            log.warning(
                "SQL import was not marked processed because the file pipeline "
                "did not return success."
            )

    except Exception as error:
        log.error(f"SQL import processing failed: {{error}}")


def safe_sql_identifier(identifier: str) -> str:
    # Keep SQL table/column identifiers conservative because they come from
    # config.json. This prevents accidental malformed INSERT statements while
    # still supporting common names like dbo.order_confirmations.
    cleaned = str(identifier or "").strip()

    if not cleaned:
        raise ValueError("SQL identifier cannot be blank.")

    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.$[]")

    if any(character not in allowed for character in cleaned):
        raise ValueError(f"Unsafe SQL identifier: {{identifier}}")

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
            row = {{
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
            }}

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
            {{
                field: row.get(field, "")
                for field in fields_with_any_value
                if not is_blank_export_value(row.get(field))
            }}
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
    insert_sql = f"INSERT INTO {{export_table}} ({{column_sql}}) VALUES ({{placeholders}})"

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
            f"SQL EXPORT SUCCESS inserted_rows={{inserted_count}} "
            f"table={{SQL_CONFIG.get('export_table')}}"
        )

    except Exception as error:
        log.error(f"SQL export failed: {{error}}")


def build_rest_export_payload(export_orders: list[dict], field_mapping: dict) -> dict:
    # Build the same cleaned, customer-shaped JSON payload used by file exports.
    customer_rows = map_export_rows_to_customer_fields(export_orders, field_mapping)

    return {{
        "source_system": "Modula WMS",
        "document_type": "EXP_ORDINI",
        "exported_at": datetime.now().isoformat(),
        "orders": group_customer_rows_for_json(customer_rows, field_mapping),
    }}


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
            headers=REST_API_CONFIG.get("headers", {{}}),
            params=REST_API_CONFIG.get("params", {{}}),
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
            headers=REST_API_CONFIG.get("headers", {{}}),
            params=REST_API_CONFIG.get("params", {{}}),
            api_key=REST_API_CONFIG.get("api_key") or None,
            api_key_header=REST_API_CONFIG.get("api_key_header", "Authorization"),
            bearer_token=bool(REST_API_CONFIG.get("bearer_token", True)),
            timeout=int(REST_API_CONFIG.get("timeout_seconds", 30)),
            max_retries=int(REST_API_CONFIG.get("max_retries", 3)),
        )

    if result.get("status") == "success":
        log.info(f"REST EXPORT SUCCESS status_code={{result.get('status_code')}} url={{export_url}}")
    else:
        log.error(f"REST EXPORT FAILED: {{result.get('error') or result.get('message')}}")


def process_customer_input_file(pipeline: FileProcessingPipeline, file_path: Path) -> dict:
    # Process customer-originated order files into Modula IMP_ORDINI XML.
    # Returning the pipeline result lets REST import mark order IDs as processed
    # only after the existing file pipeline succeeds.
    source_type = file_path.suffix.lower().lstrip(".")
    log.info(f"Detected customer {{source_type.upper()}}: {{file_path.name}}")
    result = pipeline.process(file_path=file_path)

    if result.get("status") == "success":
        xml_output = Path(result.get("xml_output"))
        wms_destination = copy_xml_to_wms_import(xml_output)

        log.info(
            f"IMPORT SUCCESS type={{result.get('source_type')}} "
            f"orders={{result.get('orders_processed')}} "
            f"xml={{xml_output.name}}"
        )
        log.info(f"WMS import copy: {{wms_destination}}")
    else:
        log.error(f"IMPORT FAILED {{result.get('error')}}")

    return result


def process_export_ordini_file(file_path: Path) -> None:
    # Process Modula-originated EXP_ORDINI XML back into customer output.
    log.info(f"Checking WMS export file: {{file_path.name}}")

    export_orders = parse_export_ordini_xml(file_path)

    if not export_orders:
        # Most often this is one of our IMP_ORDINI files in the shared IMPEXP
        # folder. Leave it alone so Modula can consume it.
        log.info(f"Skipping XML without EXP_ORDINI nodes: {{file_path.name}}")
        return

    output_path = write_customer_export(export_orders, file_path)
    post_rest_api_export(export_orders)
    process_sql_export(export_orders)
    processed_path = safe_move(file_path, WMS_EXPORT_PROCESSED_DIR)

    line_count = sum(len(order.get("lines", [])) for order in export_orders)

    log.info(
        f"EXPORT SUCCESS orders={{len(export_orders)}} "
        f"lines={{line_count}} output={{output_path.name}}"
    )
    log.info(f"Customer output written: {{output_path}}")
    log.info(f"WMS export moved to: {{processed_path}}")


def main() -> None:
    ensure_runtime_folders()

    pipeline = FileProcessingPipeline(
        profiles_dir=PROFILES_DIR,
        modula_output_dir=MODULA_OUT_DIR,
        processed_dir=PROCESSED_DIR,
        errors_dir=ERRORS_DIR,
    )

    log.info("=" * 60)
    log.info("  {customer_name} AI Middleware Runtime")
    log.info("=" * 60)
    log.info(f"  Generator version: {{CONFIG.get('generator_version', 'unknown')}}")
    log.info(f"  Package schema   : {{CONFIG.get('package_schema_version', 'unknown')}}")
    log.info(f"  Package          : {{PACKAGE_DIR}}")
    log.info(f"  Customer input   : {{INPUT_DIR}}")
    log.info(f"  Modula XML out   : {{MODULA_OUT_DIR}}")
    log.info(f"  WMS IMPEXP       : {{WMS_ORDER_IMPORT_DIR}}")
    log.info(f"  WMS export watch : {{WMS_EXPORT_WATCH_DIR}}")
    log.info(f"  Customer output  : {{CUSTOMER_OUTPUT_DIR}}")
    log.info(f"  Output format    : {{CUSTOMER_OUTPUT_FORMAT}}")
    log.info(f"  REST enabled     : {{REST_API_ENABLED}}")
    log.info(f"  REST import      : {{REST_API_IMPORT_ENABLED}}")
    log.info(f"  REST export      : {{REST_API_EXPORT_ENABLED}}")
    log.info(f"  SQL enabled      : {{SQL_ENABLED}}")
    log.info(f"  SQL import       : {{SQL_IMPORT_ENABLED}}")
    log.info(f"  SQL export       : {{SQL_EXPORT_ENABLED}}")
    enabled_integrations = ["Files"]
    if REST_API_ENABLED:
        enabled_integrations.append("REST API")
    if SQL_ENABLED:
        enabled_integrations.append("SQL/ODBC")
    log.info(f"  Active flows     : {{', '.join(enabled_integrations)}}")
    log.info(f"  Processed        : {{PROCESSED_DIR}}")
    log.info(f"  Errors           : {{ERRORS_DIR}}")
    log.info(f"  Profiles         : {{PROFILES_DIR}}")
    log.info(f"  Supported input  : {{', '.join(SUPPORTED_EXTENSIONS)}}")
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
            log.error(f"Watcher error: {{error}}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
"""

    write_text(base / "always_on_runtime.py", content)
    print("  [OK] always_on_runtime.py written")



def create_setup_rest_api_script(base: Path) -> None:
    """
    Creates a customer-friendly REST API setup utility.

    This lets a customer configure REST import/export links without manually
    editing config.json. It only updates the rest_api section and leaves the
    existing file, WMS, runtime, and profile settings unchanged.
    """

    content = '"""\nsetup_rest_api.py\n\nCustomer-friendly REST API setup utility.\n\nRun from the generated package folder:\n    python setup_rest_api.py\n\nOr double-click:\n    setup_api.bat\n\nThis script updates only the "rest_api" section of config.json.\n"""\n\nimport json\nimport urllib.error\nimport urllib.parse\nimport urllib.request\nfrom pathlib import Path\n\n\nPACKAGE_DIR = Path(__file__).resolve().parent\nCONFIG_PATH = PACKAGE_DIR / "config.json"\n\n\ndef load_config() -> dict:\n    if not CONFIG_PATH.exists():\n        raise FileNotFoundError(f"Missing config.json: {CONFIG_PATH}")\n\n    with open(CONFIG_PATH, "r", encoding="utf-8") as file:\n        return json.load(file)\n\n\ndef save_config(config: dict) -> None:\n    with open(CONFIG_PATH, "w", encoding="utf-8") as file:\n        json.dump(config, file, indent=4)\n\n\ndef ask_yes_no(prompt: str, default: bool = False) -> bool:\n    default_label = "Y/n" if default else "y/N"\n\n    while True:\n        value = input(f"{prompt} [{default_label}]: ").strip().lower()\n\n        if not value:\n            return default\n\n        if value in ["y", "yes"]:\n            return True\n\n        if value in ["n", "no"]:\n            return False\n\n        print("Please enter y or n.")\n\n\ndef ask_text(prompt: str, default: str = "") -> str:\n    if default:\n        value = input(f"{prompt} [{default}]: ").strip()\n        return value or default\n\n    return input(f"{prompt}: ").strip()\n\n\ndef ask_int(prompt: str, default: int) -> int:\n    while True:\n        value = input(f"{prompt} [{default}]: ").strip()\n\n        if not value:\n            return default\n\n        try:\n            return int(value)\n        except ValueError:\n            print("Please enter a whole number.")\n\n\ndef ask_json_object(prompt: str, default: dict | None = None) -> dict:\n    default = default or {}\n\n    print(prompt)\n    print("Leave blank for {}.")\n\n    while True:\n        value = input("> ").strip()\n\n        if not value:\n            return default\n\n        try:\n            parsed = json.loads(value)\n        except json.JSONDecodeError as error:\n            print(f"Invalid JSON: {error}")\n            continue\n\n        if not isinstance(parsed, dict):\n            print("Please enter a JSON object, for example: {\\"X-Header\\": \\"value\\"}")\n            continue\n\n        return parsed\n\n\ndef build_headers(rest_config: dict) -> dict:\n    headers = dict(rest_config.get("headers", {}) or {})\n    api_key = rest_config.get("api_key", "")\n    api_key_header = rest_config.get("api_key_header", "Authorization")\n    bearer_token = bool(rest_config.get("bearer_token", True))\n\n    if api_key:\n        headers[api_key_header] = f"Bearer {api_key}" if bearer_token else api_key\n\n    return headers\n\n\ndef test_get(url: str, rest_config: dict) -> None:\n    if not url:\n        print("Import URL is blank; skipping GET test.")\n        return\n\n    params = rest_config.get("params", {}) or {}\n    query = urllib.parse.urlencode(params)\n    test_url = f"{url}?{query}" if query else url\n\n    request = urllib.request.Request(\n        test_url,\n        method="GET",\n        headers=build_headers(rest_config),\n    )\n\n    timeout = int(rest_config.get("timeout_seconds", 30))\n\n    try:\n        with urllib.request.urlopen(request, timeout=timeout) as response:\n            body = response.read(500).decode("utf-8", errors="replace")\n            print(f"GET test succeeded. HTTP {response.status}")\n            print(f"Response preview: {body}")\n    except urllib.error.HTTPError as error:\n        print(f"GET test failed. HTTP {error.code}: {error.reason}")\n    except Exception as error:\n        print(f"GET test failed: {error}")\n\n\ndef test_export_post(url: str, rest_config: dict) -> None:\n    if not url:\n        print("Export URL is blank; skipping POST/PUT test.")\n        return\n\n    payload = {\n        "source_system": "Modula WMS",\n        "document_type": "REST_SETUP_TEST",\n        "orders": [\n            {\n                "order_id": "SETUP-TEST",\n                "lines": [\n                    {\n                        "item": "BRG-100",\n                        "quantity": "1",\n                    }\n                ],\n            }\n        ],\n    }\n\n    data = json.dumps(payload).encode("utf-8")\n    headers = build_headers(rest_config)\n    headers["Content-Type"] = "application/json"\n\n    request = urllib.request.Request(\n        url,\n        data=data,\n        method=rest_config.get("export_method", "POST").upper(),\n        headers=headers,\n    )\n\n    timeout = int(rest_config.get("timeout_seconds", 30))\n\n    try:\n        with urllib.request.urlopen(request, timeout=timeout) as response:\n            body = response.read(500).decode("utf-8", errors="replace")\n            print(f"Export test succeeded. HTTP {response.status}")\n            print(f"Response preview: {body}")\n    except urllib.error.HTTPError as error:\n        print(f"Export test failed. HTTP {error.code}: {error.reason}")\n    except Exception as error:\n        print(f"Export test failed: {error}")\n\n\ndef configure_rest_api(config: dict) -> dict:\n    rest_config = dict(config.get("rest_api", {}) or {})\n\n    print("=" * 70)\n    print("REST API SETUP")\n    print("=" * 70)\n    print("This setup updates only config.json -> rest_api.")\n    print("Leave optional values blank if the customer API does not need them.")\n    print("=" * 70)\n\n    import_enabled = ask_yes_no(\n        "Enable REST API import? Customer API -> Modula",\n        bool(rest_config.get("import_enabled", False)),\n    )\n\n    export_enabled = ask_yes_no(\n        "Enable REST API export? Modula -> Customer API",\n        bool(rest_config.get("export_enabled", False)),\n    )\n\n    rest_config["enabled"] = import_enabled or export_enabled\n    rest_config["import_enabled"] = import_enabled\n    rest_config["export_enabled"] = export_enabled\n\n    if import_enabled:\n        rest_config["import_url"] = ask_text(\n            "Import GET URL",\n            rest_config.get("import_url", ""),\n        )\n        rest_config["records_key"] = ask_text(\n            "Records key/path in API response",\n            rest_config.get("records_key", "orders"),\n        )\n\n    if export_enabled:\n        rest_config["export_url"] = ask_text(\n            "Export POST/PUT URL",\n            rest_config.get("export_url", ""),\n        )\n\n        export_method = ask_text(\n            "Export method",\n            rest_config.get("export_method", "POST"),\n        ).upper()\n\n        if export_method not in ["POST", "PUT"]:\n            print("Unsupported export method entered; defaulting to POST.")\n            export_method = "POST"\n\n        rest_config["export_method"] = export_method\n        rest_config["batch_key"] = ask_text(\n            "Export batch key",\n            rest_config.get("batch_key", "orders"),\n        )\n\n    rest_config["headers"] = ask_json_object(\n        "Optional request headers as JSON object",\n        rest_config.get("headers", {}),\n    )\n\n    rest_config["params"] = ask_json_object(\n        "Optional query params as JSON object",\n        rest_config.get("params", {}),\n    )\n\n    rest_config["api_key"] = ask_text(\n        "API key/token, optional",\n        rest_config.get("api_key", ""),\n    )\n\n    if rest_config.get("api_key"):\n        rest_config["api_key_header"] = ask_text(\n            "API key header",\n            rest_config.get("api_key_header", "Authorization"),\n        )\n        rest_config["bearer_token"] = ask_yes_no(\n            "Use Bearer token format?",\n            bool(rest_config.get("bearer_token", True)),\n        )\n    else:\n        rest_config["api_key_header"] = rest_config.get(\n            "api_key_header",\n            "Authorization",\n        )\n        rest_config["bearer_token"] = bool(rest_config.get("bearer_token", True))\n\n    rest_config["poll_interval_seconds"] = ask_int(\n        "REST import poll interval in seconds",\n        int(rest_config.get("poll_interval_seconds", 60)),\n    )\n\n    rest_config["timeout_seconds"] = ask_int(\n        "Request timeout in seconds",\n        int(rest_config.get("timeout_seconds", 30)),\n    )\n\n    rest_config["max_retries"] = ask_int(\n        "Max request retries",\n        int(rest_config.get("max_retries", 3)),\n    )\n\n    config["rest_api"] = rest_config\n    return config\n\n\ndef main() -> None:\n    config = load_config()\n    config = configure_rest_api(config)\n    save_config(config)\n\n    print()\n    print("REST API settings saved to config.json.")\n\n    rest_config = config.get("rest_api", {})\n\n    if rest_config.get("import_enabled") and ask_yes_no(\n        "Test REST import GET now?",\n        True,\n    ):\n        test_get(rest_config.get("import_url", ""), rest_config)\n\n    if rest_config.get("export_enabled") and ask_yes_no(\n        "Send a small test export POST/PUT now?",\n        False,\n    ):\n        test_export_post(rest_config.get("export_url", ""), rest_config)\n\n    print()\n    print("Setup complete. You can now run start.bat or always_on_runtime.py.")\n\n\nif __name__ == "__main__":\n    main()\n'
    write_text(base / "setup_rest_api.py", content)
    print("  [OK] setup_rest_api.py written")


def create_setup_api_bat(base: Path) -> None:
    content = '@echo off\necho Modula Middleware REST API Setup\necho.\n\ncd /d %~dp0\npython setup_rest_api.py\n\npause\n'
    write_text(base / "setup_api.bat", content)
    print("  [OK] setup_api.bat written")



def create_setup_sql_odbc_script(base: Path) -> None:
    """
    Creates a customer-friendly SQL / ODBC setup utility.

    This is intentionally configuration-only for now. It lets us verify that
    the customer can enter and test a database connection before we wire SQL
    polling/import/export into always_on_runtime.py.
    """

    content = '"""\nsetup_sql_odbc.py\n\nCustomer-friendly SQL / ODBC setup utility.\n\nRun from the generated package folder:\n    python setup_sql_odbc.py\n\nOr double-click:\n    setup_database.bat\n\nThis script updates only the "sql" section of config.json.\n"""\n\nimport json\nimport sqlite3\nfrom pathlib import Path\n\n\nPACKAGE_DIR = Path(__file__).resolve().parent\nCONFIG_PATH = PACKAGE_DIR / "config.json"\n\n\ndef load_config() -> dict:\n    if not CONFIG_PATH.exists():\n        raise FileNotFoundError(f"Missing config.json: {CONFIG_PATH}")\n\n    with open(CONFIG_PATH, "r", encoding="utf-8") as file:\n        return json.load(file)\n\n\ndef save_config(config: dict) -> None:\n    with open(CONFIG_PATH, "w", encoding="utf-8") as file:\n        json.dump(config, file, indent=4)\n\n\ndef ask_yes_no(prompt: str, default: bool = False) -> bool:\n    default_label = "Y/n" if default else "y/N"\n\n    while True:\n        value = input(f"{prompt} [{default_label}]: ").strip().lower()\n\n        if not value:\n            return default\n\n        if value in ["y", "yes"]:\n            return True\n\n        if value in ["n", "no"]:\n            return False\n\n        print("Please enter y or n.")\n\n\ndef ask_text(prompt: str, default: str = "") -> str:\n    if default:\n        value = input(f"{prompt} [{default}]: ").strip()\n        return value or default\n\n    return input(f"{prompt}: ").strip()\n\n\ndef ask_int(prompt: str, default: int) -> int:\n    while True:\n        value = input(f"{prompt} [{default}]: ").strip()\n\n        if not value:\n            return default\n\n        try:\n            return int(value)\n        except ValueError:\n            print("Please enter a whole number.")\n\n\ndef ask_json_object(prompt: str, default: dict | None = None) -> dict:\n    default = default or {}\n\n    print(prompt)\n    print("Leave blank for {}.")\n\n    while True:\n        value = input("> ").strip()\n\n        if not value:\n            return default\n\n        try:\n            parsed = json.loads(value)\n        except json.JSONDecodeError as error:\n            print(f"Invalid JSON: {error}")\n            continue\n\n        if not isinstance(parsed, dict):\n            print("Please enter a JSON object, for example: {\\"order_id\\": \\"OrderNumber\\"}")\n            continue\n\n        return parsed\n\n\ndef resolve_package_path(path_value: str) -> Path:\n    path = Path(path_value)\n\n    if path.is_absolute():\n        return path\n\n    return PACKAGE_DIR / path\n\n\ndef test_sql_connection(sql_config: dict) -> bool:\n    database_type = str(sql_config.get("database_type", "sqlite")).lower()\n    connection_string = sql_config.get("connection_string", "")\n    timeout = int(sql_config.get("timeout_seconds", 30))\n\n    if not connection_string:\n        print("Connection string is blank; cannot test connection.")\n        return False\n\n    try:\n        if database_type == "sqlite":\n            db_path = resolve_package_path(connection_string)\n            db_path.parent.mkdir(parents=True, exist_ok=True)\n\n            with sqlite3.connect(str(db_path), timeout=timeout) as connection:\n                cursor = connection.cursor()\n                cursor.execute("SELECT 1 AS connection_test")\n                result = cursor.fetchone()\n\n            print(f"SQLite connection test succeeded: {result[0]}")\n            print(f"Database path: {db_path}")\n            return True\n\n        if database_type in ["odbc", "sql_server"]:\n            try:\n                import pyodbc\n            except ImportError:\n                print("pyodbc is not installed. Install it with: pip install pyodbc")\n                return False\n\n            connection = pyodbc.connect(connection_string, timeout=timeout)\n            cursor = connection.cursor()\n            cursor.execute("SELECT 1 AS connection_test")\n            result = cursor.fetchone()\n            cursor.close()\n            connection.close()\n\n            print(f"ODBC connection test succeeded: {result[0]}")\n            return True\n\n        print(f"Unsupported database_type: {database_type}")\n        return False\n\n    except Exception as error:\n        print(f"SQL connection test failed: {error}")\n        return False\n\n\ndef create_sqlite_demo_database(sql_config: dict) -> None:\n    database_type = str(sql_config.get("database_type", "sqlite")).lower()\n\n    if database_type != "sqlite":\n        print("Demo database creation is only available for SQLite.")\n        return\n\n    db_path = resolve_package_path(sql_config.get("connection_string", "runtime/sql/customer_orders.db"))\n    db_path.parent.mkdir(parents=True, exist_ok=True)\n\n    with sqlite3.connect(str(db_path)) as connection:\n        cursor = connection.cursor()\n\n        cursor.execute(\n            """\n            CREATE TABLE IF NOT EXISTS orders_to_modula (\n                order_id TEXT NOT NULL,\n                customer_name TEXT,\n                item TEXT NOT NULL,\n                quantity REAL NOT NULL\n            )\n            """\n        )\n\n        cursor.execute(\n            """\n            CREATE TABLE IF NOT EXISTS order_confirmations (\n                order_id TEXT,\n                item TEXT,\n                quantity TEXT,\n                operation_type TEXT,\n                exported_at TEXT\n            )\n            """\n        )\n\n        cursor.execute("DELETE FROM orders_to_modula")\n\n        cursor.executemany(\n            """\n            INSERT INTO orders_to_modula (\n                order_id,\n                customer_name,\n                item,\n                quantity\n            ) VALUES (?, ?, ?, ?)\n            """,\n            [\n                ("PO10001", "Brawl Industries", "BRG-100", 10),\n                ("PO10001", "Brawl Industries", "CBL-100", 5),\n                ("PO10002", "Brawl Industries", "CBL-200", 8),\n            ],\n        )\n\n        connection.commit()\n\n    print(f"SQLite demo database created/updated: {db_path}")\n    print("Demo import table: orders_to_modula")\n    print("Demo export table: order_confirmations")\n\n\ndef configure_sql(config: dict) -> dict:\n    sql_config = dict(config.get("sql", {}) or {})\n\n    print("=" * 70)\n    print("SQL / ODBC SETUP")\n    print("=" * 70)\n    print("This setup updates only config.json -> sql.")\n    print("SQLite is recommended first for testing. Use ODBC later for SQL Server.")\n    print("=" * 70)\n\n    import_enabled = ask_yes_no(\n        "Enable SQL import? Database -> Modula",\n        bool(sql_config.get("import_enabled", False)),\n    )\n\n    export_enabled = ask_yes_no(\n        "Enable SQL export? Modula -> Database",\n        bool(sql_config.get("export_enabled", False)),\n    )\n\n    sql_config["enabled"] = import_enabled or export_enabled\n    sql_config["import_enabled"] = import_enabled\n    sql_config["export_enabled"] = export_enabled\n\n    database_type = ask_text(\n        "Database type: sqlite, odbc, or sql_server",\n        sql_config.get("database_type", "sqlite"),\n    ).lower()\n\n    if database_type not in ["sqlite", "odbc", "sql_server"]:\n        print("Unsupported database type entered; defaulting to sqlite.")\n        database_type = "sqlite"\n\n    sql_config["database_type"] = database_type\n\n    default_connection = sql_config.get(\n        "connection_string",\n        "runtime/sql/customer_orders.db",\n    )\n\n    sql_config["connection_string"] = ask_text(\n        "Connection string or SQLite database path",\n        default_connection,\n    )\n\n    if import_enabled:\n        sql_config["import_query"] = ask_text(\n            "Import SELECT query",\n            sql_config.get("import_query", "SELECT * FROM orders_to_modula"),\n        )\n\n        sql_config["processed_key_column"] = ask_text(\n            "Processed key column used to prevent duplicate imports",\n            sql_config.get("processed_key_column", "order_id"),\n        )\n\n    if export_enabled:\n        sql_config["export_table"] = ask_text(\n            "Export confirmation table",\n            sql_config.get("export_table", "order_confirmations"),\n        )\n\n    sql_config["field_mapping"] = ask_json_object(\n        "Optional SQL field mapping as JSON object",\n        sql_config.get("field_mapping", {}),\n    )\n\n    sql_config["poll_interval_seconds"] = ask_int(\n        "SQL import poll interval in seconds",\n        int(sql_config.get("poll_interval_seconds", 60)),\n    )\n\n    sql_config["timeout_seconds"] = ask_int(\n        "Database timeout in seconds",\n        int(sql_config.get("timeout_seconds", 30)),\n    )\n\n    config["sql"] = sql_config\n    return config\n\n\ndef main() -> None:\n    config = load_config()\n    config = configure_sql(config)\n\n    sql_config = config.get("sql", {})\n\n    print()\n    if ask_yes_no("Test SQL connection now?", True):\n        test_sql_connection(sql_config)\n\n    if sql_config.get("database_type") == "sqlite" and ask_yes_no(\n        "Create/update SQLite demo tables and sample orders?",\n        True,\n    ):\n        create_sqlite_demo_database(sql_config)\n\n    save_config(config)\n\n    print()\n    print("SQL / ODBC settings saved to config.json.")\n    print("Setup complete. You can now run start.bat or always_on_runtime.py.")\n\n\nif __name__ == "__main__":\n    main()\n'
    write_text(base / "setup_sql_odbc.py", content)
    print("  [OK] setup_sql_odbc.py written")


def create_setup_database_bat(base: Path) -> None:
    content = '@echo off\necho Modula Middleware SQL / ODBC Setup\necho.\n\ncd /d %~dp0\npython setup_sql_odbc.py\n\npause\n'
    write_text(base / "setup_database.bat", content)
    print("  [OK] setup_database.bat written")


def create_self_test_script(base: Path) -> None:
    """
    Creates a generated package self-test utility.

    This script checks config.json, expected folders, and core imports without
    starting the always-on runtime watcher.
    """

    content = '"""\nself_test.py\n\nGenerated package validation utility.\n\nRun from the generated package folder:\n    python self_test.py\n\nOr double-click:\n    self_test.bat\n"""\n\nimport importlib\nimport json\nimport sys\nfrom pathlib import Path\n\n\nPACKAGE_DIR = Path(__file__).resolve().parent\nCONFIG_PATH = PACKAGE_DIR / "config.json"\n\nif str(PACKAGE_DIR) not in sys.path:\n    sys.path.insert(0, str(PACKAGE_DIR))\n\n\nREQUIRED_PATHS = [\n    "always_on_runtime.py",\n    "config.json",\n    "start.bat",\n    "setup_api.bat",\n    "setup_rest_api.py",\n    "setup_database.bat",\n    "setup_sql_odbc.py",\n    "src",\n    "agents",\n    "runtime/customer_input",\n    "runtime/customer_output",\n    "runtime/modula_output",\n    "runtime/processed",\n    "runtime/errors",\n    "runtime/profiles",\n    "runtime/sql",\n]\n\nREQUIRED_IMPORTS = [\n    "src.pipeline.file_processing_pipeline",\n    "src.connectors.rest_api_connector",\n    "src.connectors.db_connector",\n    "agents.openai_field_mapping_agent",\n]\n\n\ndef check_path(relative_path: str) -> bool:\n    path = PACKAGE_DIR / relative_path\n    if path.exists():\n        print(f"[OK] Path exists: {relative_path}")\n        return True\n\n    print(f"[FAIL] Missing path: {relative_path}")\n    return False\n\n\ndef check_import(module_name: str) -> bool:\n    try:\n        importlib.import_module(module_name)\n        print(f"[OK] Import works: {module_name}")\n        return True\n    except Exception as error:\n        print(f"[FAIL] Import failed: {module_name} -> {error}")\n        return False\n\n\ndef check_config() -> bool:\n    try:\n        with open(CONFIG_PATH, "r", encoding="utf-8") as file:\n            config = json.load(file)\n\n        print(f"[OK] Config loads: {CONFIG_PATH.name}")\n        print(f"     Customer: {config.get(\'customer_name\')}")\n        print(f"     Generator version: {config.get(\'generator_version\', \'unknown\')}")\n        print(f"     REST enabled: {config.get(\'rest_api\', {}).get(\'enabled\')}")\n        print(f"     SQL enabled: {config.get(\'sql\', {}).get(\'enabled\')}")\n        return True\n\n    except Exception as error:\n        print(f"[FAIL] Config check failed: {error}")\n        return False\n\n\ndef main() -> None:\n    print("=" * 70)\n    print("MODULA MIDDLEWARE PACKAGE SELF-TEST")\n    print("=" * 70)\n    print(f"Package: {PACKAGE_DIR}")\n    print()\n\n    checks = []\n    checks.append(check_config())\n\n    for relative_path in REQUIRED_PATHS:\n        checks.append(check_path(relative_path))\n\n    for module_name in REQUIRED_IMPORTS:\n        checks.append(check_import(module_name))\n\n    print()\n    print("=" * 70)\n\n    if all(checks):\n        print("SELF-TEST PASSED")\n        print("The generated package structure and imports look valid.")\n        sys.exit(0)\n\n    print("SELF-TEST FAILED")\n    print("Review the failed checks above before deploying this package.")\n    sys.exit(1)\n\n\nif __name__ == "__main__":\n    main()\n'
    write_text(base / "self_test.py", content)
    print("  [OK] self_test.py written")


def create_self_test_bat(base: Path) -> None:
    content = '@echo off\necho Modula Middleware Package Self-Test\necho.\n\ncd /d %~dp0\npython self_test.py\n\npause\n'
    write_text(base / "self_test.bat", content)
    print("  [OK] self_test.bat written")


def create_start_bat(base: Path, customer_name: str) -> None:
    content = f"""@echo off
echo Starting {customer_name} AI Middleware Runtime...
echo.

cd /d %~dp0
python always_on_runtime.py

pause
"""
    write_text(base / "start.bat", content)
    print("  [OK] start.bat written")


def create_readme(
    base: Path,
    customer_name: str,
    source_type: str,
    wms_order_import_path: str,
) -> None:
    content = f"""# {customer_name} Portable Runtime Package

Generated by Modula WMS AI Middleware  
{datetime.now().strftime("%Y-%m-%d %H:%M")}

## Supported customer input files

This runtime package watches `runtime/customer_input/` for:

- `.csv`
- `.json`
- `.xml`

The configured primary source type is `{source_type}`, but the watcher accepts all three supported file types.

## Import flow: customer file to Modula

1. Double-click `start.bat`.
2. Drop a CSV, JSON, or XML order file into:

       runtime/customer_input/

3. The agent will:
   - Detect the file automatically.
   - Route CSV, JSON, and XML files through the correct parser path.
   - Use AI to map CSV columns to Modula WMS fields, or reuse a saved CSV profile.
   - Parse JSON/XML files through the packaged parser classes.
   - Convert the order data into Modula `IMP_ORDINI` XML.
   - Write the XML into `runtime/modula_output/`.
   - Copy the XML into the configured Modula IMPEXP folder.
   - Move the original input file to `runtime/processed/`.

## Export flow: Modula back to customer

The runtime also watches the configured Modula IMPEXP folder for `EXP_ORDINI` XML files.

When an `EXP_ORDINI` file appears, the runtime will:

- Parse the Modula export order confirmation.
- Convert it back into the configured customer output format.
- Write the customer-facing file into:

       runtime/customer_output/

- Move the processed Modula export XML into:

       runtime/wms_export_processed/

The customer output format is controlled in `config.json`:

       "customer_output": {{
           "format": "{source_type}"
       }}

Supported customer output formats are:

- `json`
- `csv`
- `xml`

The export conversion uses the saved profile in `runtime/profiles/`.
That profile contains the OpenAI/customer mapping created during import, so
fields like `order_id`, `item`, and `quantity` are written back using the
customer's original column or field names.

## Modula IMPEXP path

The current Modula IMPEXP path is configured in `config.json`:

       {wms_order_import_path}

This path is used for both:

- Generated `IMP_ORDINI` files going into Modula.
- Modula `EXP_ORDINI` files coming back from Modula.

For your current setup, this should be:

       C:\\SystemLogistics\\IMPEXP

## Folder structure

    runtime/
    ├── customer_input/          <- drop customer CSV, JSON, or XML files here
    ├── customer_output/         <- customer-facing export files are written here
    ├── modula_output/           <- generated Modula IMP_ORDINI XML appears here
    ├── wms_export_processed/    <- processed Modula EXP_ORDINI XML files
    ├── processed/               <- successfully processed customer input files
    ├── errors/                  <- failed customer input files
    └── profiles/                <- saved AI mapping profiles

## Files

- `always_on_runtime.py` — the AI middleware runtime agent
- `start.bat` — launches the runtime
- `setup_api.bat` — launches REST API setup
- `setup_rest_api.py` — updates the REST API section of `config.json`
- `setup_database.bat` — launches SQL / ODBC setup
- `setup_sql_odbc.py` — updates the SQL section of `config.json`
- `config.json` — customer, WMS path, and output format settings
- `src/` — portable runtime engine
- `agents/` — portable AI and generator logic
- `parsing/` — included only if your current project still keeps parser modules outside `src/`

## Regenerate with a different customer name

From the project root:

       python generate_test_package.py Ford
       python generate_test_package.py "Acme Manufacturing"

You can also set the customer input/output format:

       python generate_test_package.py Ford --source-type json
       python generate_test_package.py Ford --source-type xml

## REST API integrations

REST API support is included in the generated runtime but disabled by default.
To configure REST without manually editing JSON, double-click:

       setup_api.bat

The setup utility updates only the `rest_api` section of `config.json`.

REST import flow:

- Polls `rest_api.import_url`.
- Converts API JSON records into the same order structure used by file imports.
- Reuses the existing pipeline to generate Modula `IMP_ORDINI` XML.

REST export flow:

- Uses the same cleaned profile-driven `EXP_ORDINI` payload as local JSON exports.
- Sends confirmations to `rest_api.export_url` with POST or PUT.

## SQL / ODBC integrations

SQL / ODBC support is included in the generated configuration but disabled by default.
To configure a database connection without manually editing JSON, double-click:

       setup_database.bat

The setup utility updates only the `sql` section of `config.json`.

Recommended first test:

- Use `database_type` = `sqlite`.
- Let the setup utility create the demo SQLite database.
- Confirm the database connection succeeds.

SQL import/export runtime polling will be wired in after the setup and connection
configuration are verified.

## Package self-test

Before deploying or sending the package to a customer, run:

       self_test.bat

The self-test checks the generated config, required folders, and core Python imports without starting the always-on watcher.

## Notes

- CSV files use AI field mapping once per new profile, then the saved profile is reused.
- JSON/XML import behavior depends on the parser and pipeline files copied from your current project.
- Export conversion uses the saved OpenAI/customer mapping profile to rebuild customer-shaped JSON, CSV, or XML output.
- To force a CSV re-mapping, delete the profile from `runtime/profiles/`.
- This package can be copied outside the VS Code project folder because it includes local `src/` and `agents/` folders.
- The computer still needs Python and required dependencies installed.
"""
    write_text(base / "README.md", content)
    print("  [OK] README.md written")


def generate() -> None:
    args = parse_args()

    customer_name = args.customer_name
    source_type = args.source_type
    wms_order_import_path = args.wms_order_import_path

    key = safe_name(customer_name)
    base = Path("generated_integrations") / key

    print(f"\nGenerating portable package for: {customer_name}")
    print(f"Output folder: {base}\n")

    # Make sure this package generator is not building a package that is missing
    # the parser/pipeline files needed for JSON and XML support.
    validate_runtime_engine_files()

    create_runtime_folders(base)
    copy_runtime_engine(base)
    create_config(
        base=base,
        customer_name=customer_name,
        source_type=source_type,
        wms_order_import_path=wms_order_import_path,
    )
    create_runtime_script(base, customer_name)
    create_setup_rest_api_script(base)
    create_setup_api_bat(base)
    create_setup_sql_odbc_script(base)
    create_setup_database_bat(base)
    create_self_test_script(base)
    create_self_test_bat(base)
    create_start_bat(base, customer_name)
    create_readme(
        base=base,
        customer_name=customer_name,
        source_type=source_type,
        wms_order_import_path=wms_order_import_path,
    )

    print(f"\nDone. Package ready at: {base}")
    print("\nNext steps:")
    print(f"  1. Run: python generated_integrations\\{key}\\always_on_runtime.py")
    print(f"  2. Optional REST setup: generated_integrations\\{key}\\setup_api.bat")
    print(f"  3. Optional SQL setup: generated_integrations\\{key}\\setup_database.bat")
    print(f"  4. Optional self-test: generated_integrations\\{key}\\self_test.bat")
    print(f"  5. Or double-click: generated_integrations\\{key}\\start.bat")
    print(
        f"  6. Drop a CSV, JSON, or XML file into: "
        f"generated_integrations\\{key}\\runtime\\customer_input"
    )
    print(f"  7. Watch customer exports in: generated_integrations\\{key}\\runtime\\customer_output")
    print("\nOptional examples:")
    print("  python generate_test_package.py Ford")
    print('  python generate_test_package.py "Acme Manufacturing"')
    print("  python generate_test_package.py Ford --source-type json")
    print("  python generate_test_package.py Ford --source-type xml")
    print(
        '  python generate_test_package.py Ford '
        '--wms-order-import-path "C:\\\\Modula\\\\WMS\\\\IMPORT\\\\ORDINI"'
    )


if __name__ == "__main__":
    generate()