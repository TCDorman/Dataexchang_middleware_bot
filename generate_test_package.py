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
        ├── always_on_runtime.py
        ├── config.json
        ├── README.md
        ├── agents/
        ├── src/
        └── runtime/
            ├── customer_input/       <- drop customer CSV files here
            ├── customer_output/
            ├── modula_output/        <- generated XML appears here
            ├── processed/
            ├── errors/
            ├── profiles/
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
DEFAULT_WMS_ORDER_IMPORT_PATH = "runtime/wms_order_import_test"


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
        help=f"Source type. Default: {DEFAULT_SOURCE_TYPE}",
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


def create_runtime_folders(base: Path) -> None:
    folders = [
        base / "runtime" / "customer_input",
        base / "runtime" / "customer_output",
        base / "runtime" / "modula_output",
        base / "runtime" / "processed",
        base / "runtime" / "errors",
        base / "runtime" / "profiles",
        base / "runtime" / "wms_order_import_test",
    ]
    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)
    print("  [OK] Runtime folders created")


def copy_runtime_engine(base: Path) -> None:
    copy_folder(Path("src"), base / "src")
    copy_folder(Path("agents"), base / "agents")
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
        "target_system": TARGET_SYSTEM,
        "target_format": TARGET_FORMAT,
        "created_at": datetime.now().isoformat(),
        "runtime": {
            "input_dir": "runtime/customer_input",
            "output_dir": "runtime/customer_output",
            "modula_output_dir": "runtime/modula_output",
            "processed_dir": "runtime/processed",
            "errors_dir": "runtime/errors",
            "profiles_dir": "runtime/profiles",
        },
        "wms": {
            "ordini_import_path": wms_order_import_path,
        },
    }
    write_json(base / "config.json", config)
    print("  [OK] config.json written")


def create_runtime_script(base: Path, customer_name: str) -> None:
    content = f"""\"\"\"
always_on_runtime.py — {customer_name} AI Middleware Runtime

Portable runtime package.

Watches runtime/customer_input for CSV files.
Converts customer CSV files into Modula IMP_ORDINI XML.
Copies generated XML into the configured WMS order import path.
\"\"\"

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

POLL_INTERVAL = 5


try:
    from src.pipeline.file_processing_pipeline import FileProcessingPipeline
except ImportError as error:
    log.error(f"Could not import FileProcessingPipeline: {{error}}")
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
    log.info(f"  Package    : {{PACKAGE_DIR}}")
    log.info(f"  Watching   : {{INPUT_DIR}}")
    log.info(f"  XML out    : {{MODULA_OUT_DIR}}")
    log.info(f"  WMS import : {{WMS_ORDER_IMPORT_DIR}}")
    log.info(f"  Processed  : {{PROCESSED_DIR}}")
    log.info(f"  Errors     : {{ERRORS_DIR}}")
    log.info(f"  Profiles   : {{PROFILES_DIR}}")
    log.info("  Drop a CSV into customer_input to begin.")
    log.info("=" * 60)

    seen = set()

    while True:
        try:
            files = list(INPUT_DIR.iterdir())

            if not files:
                log.info("Waiting... no files found in customer_input")

            for file_path in files:
                log.info(f"Found file: {{file_path.name}}")

                if not file_path.is_file():
                    continue

                if file_path.suffix.lower() != ".csv":
                    log.warning(f"Skipping non-CSV file: {{file_path.name}}")
                    continue

                if file_path.name in seen:
                    continue

                seen.add(file_path.name)

                log.info(f"Detected CSV: {{file_path.name}}")
                result = pipeline.process(file_path=file_path)

                if result.get("status") == "success":
                    xml_output = Path(result.get("xml_output"))
                    wms_destination = copy_xml_to_wms_import(xml_output)

                    log.info(
                        f"SUCCESS orders={{result.get('orders_processed')}} "
                        f"xml={{xml_output.name}}"
                    )
                    log.info(f"WMS import copy: {{wms_destination}}")
                else:
                    log.error(f"FAILED {{result.get('error')}}")

        except KeyboardInterrupt:
            log.info("Shutdown requested — stopping runtime.")
            break

        except Exception as error:
            log.error(f"Watcher error: {{error}}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
"""

    write_text(base / "always_on_runtime.py", content)
    print("  [OK] always_on_runtime.py written")


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

## How to use

1. Double-click `start.bat`.
2. Drop a `{source_type.upper()}` file into:

       runtime/customer_input/

3. The agent will:
   - Detect the file automatically.
   - Use AI to map your columns to Modula WMS fields, or reuse a saved profile.
   - Save reusable profiles to `runtime/profiles/`.
   - Convert your data into Modula `IMP_ORDINI` XML.
   - Write the XML into `runtime/modula_output/`.
   - Copy the XML into the configured WMS order import path.
   - Move your original CSV to `runtime/processed/`.

## WMS order import path

The current WMS order import path is configured in `config.json`:

       {wms_order_import_path}

By default, this test package uses:

       runtime/wms_order_import_test/

When ready, change `config.json` to the real Modula WMS import folder, for example:

       C:\\Modula\\WMS\\IMPORT\\ORDINI

## Folder structure

    runtime/
    ├── customer_input/         <- drop customer CSV files here
    ├── modula_output/          <- generated Modula XML appears here
    ├── wms_order_import_test/  <- default test WMS import folder
    ├── customer_output/        <- future customer export files
    ├── processed/              <- successfully processed CSV files
    ├── errors/                 <- failed CSV files
    └── profiles/               <- saved AI mapping profiles

## Files

- `always_on_runtime.py` — the AI middleware runtime agent
- `start.bat` — launches the runtime
- `config.json` — customer and WMS path settings
- `src/` — portable runtime engine
- `agents/` — portable AI and generator logic

## Regenerate with a different customer name

From the project root:

       python generate_test_package.py Ford
       python generate_test_package.py "Acme Manufacturing"

## Notes

- The AI field mapping runs once per new profile, then the saved profile is reused.
- To force a re-mapping, delete the profile from `runtime/profiles/`.
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

    create_runtime_folders(base)
    copy_runtime_engine(base)
    create_config(
        base=base,
        customer_name=customer_name,
        source_type=source_type,
        wms_order_import_path=wms_order_import_path,
    )
    create_runtime_script(base, customer_name)
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
    print(f"  2. Or double-click: generated_integrations\\{key}\\start.bat")
    print(f"  3. Drop your CSV into: generated_integrations\\{key}\\runtime\\customer_input")
    print("\nOptional examples:")
    print("  python generate_test_package.py Ford")
    print('  python generate_test_package.py "Acme Manufacturing"')
    print(
        '  python generate_test_package.py Ford '
        '--wms-order-import-path "C:\\\\Modula\\\\WMS\\\\IMPORT\\\\ORDINI"'
    )


if __name__ == "__main__":
    generate()
