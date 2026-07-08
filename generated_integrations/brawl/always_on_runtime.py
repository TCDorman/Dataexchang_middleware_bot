"""
always_on_runtime.py — Brawl AI Middleware Runtime

Portable runtime package.

Watches runtime/customer_input for CSV, JSON, and XML files.
Converts customer order files into Modula IMP_ORDINI XML.
Copies generated XML into the configured WMS order import path.
"""

import json
import logging
import shutil
import sys
import time
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

INPUT_DIR = resolve_package_path(
    RUNTIME_CONFIG.get("input_dir", "runtime/customer_input")
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
WMS_ORDER_IMPORT_DIR = resolve_package_path(
    WMS_CONFIG.get("ordini_import_path", "runtime/wms_order_import_test")
)

SUPPORTED_EXTENSIONS = [
    ext.lower()
    for ext in CONFIG.get("supported_file_extensions", DEFAULT_SUPPORTED_EXTENSIONS)
]
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
        MODULA_OUT_DIR,
        PROCESSED_DIR,
        ERRORS_DIR,
        PROFILES_DIR,
        WMS_ORDER_IMPORT_DIR,
    ]:
        folder.mkdir(parents=True, exist_ok=True)


def copy_xml_to_wms_import(xml_output: Path) -> Path:
    WMS_ORDER_IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    destination = WMS_ORDER_IMPORT_DIR / xml_output.name
    shutil.copy2(xml_output, destination)
    return destination


def is_supported_input_file(file_path: Path) -> bool:
    """
    Runtime file filter.

    CSV still uses AI field mapping in the pipeline. JSON and XML are passed to
    their parser implementations and then flow into the same Modula XML output
    formatter. Unsupported files stay in customer_input and are ignored.
    """

    return file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS


def main() -> None:
    ensure_runtime_folders()

    pipeline = FileProcessingPipeline(
        profiles_dir=PROFILES_DIR,
        modula_output_dir=MODULA_OUT_DIR,
        processed_dir=PROCESSED_DIR,
        errors_dir=ERRORS_DIR,
    )

    log.info("=" * 60)
    log.info("  Brawl AI Middleware Runtime")
    log.info("=" * 60)
    log.info(f"  Package    : {PACKAGE_DIR}")
    log.info(f"  Watching   : {INPUT_DIR}")
    log.info(f"  XML out    : {MODULA_OUT_DIR}")
    log.info(f"  WMS import : {WMS_ORDER_IMPORT_DIR}")
    log.info(f"  Processed  : {PROCESSED_DIR}")
    log.info(f"  Errors     : {ERRORS_DIR}")
    log.info(f"  Profiles   : {PROFILES_DIR}")
    log.info(f"  Supported  : {', '.join(SUPPORTED_EXTENSIONS)}")
    log.info("  Drop a CSV, JSON, or XML file into customer_input to begin.")
    log.info("=" * 60)

    seen = set()

    while True:
        try:
            files = list(INPUT_DIR.iterdir())

            if not files:
                log.info("Waiting... no files found in customer_input")

            for file_path in files:
                log.info(f"Found file: {file_path.name}")

                if not file_path.is_file():
                    continue

                if not is_supported_input_file(file_path):
                    log.warning(
                        f"Skipping unsupported file type: {file_path.name} "
                        f"supported={SUPPORTED_EXTENSIONS}"
                    )
                    continue

                # Prevents the same file from being processed twice in one run.
                # The pipeline also moves successful files to processed/.
                if file_path.name in seen:
                    continue

                seen.add(file_path.name)

                source_type = file_path.suffix.lower().lstrip(".")
                log.info(f"Detected {source_type.upper()}: {file_path.name}")
                result = pipeline.process(file_path=file_path)

                if result.get("status") == "success":
                    xml_output = Path(result.get("xml_output"))
                    wms_destination = copy_xml_to_wms_import(xml_output)

                    log.info(
                        f"SUCCESS type={result.get('source_type')} "
                        f"orders={result.get('orders_processed')} "
                        f"xml={xml_output.name}"
                    )
                    log.info(f"WMS import copy: {wms_destination}")
                else:
                    log.error(f"FAILED {result.get('error')}")

        except KeyboardInterrupt:
            log.info("Shutdown requested — stopping runtime.")
            break

        except Exception as error:
            log.error(f"Watcher error: {error}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
