"""
self_test.py

Generated package validation utility.

Run from the generated package folder:
    python self_test.py

Or double-click:
    self_test.bat
"""

import importlib
import json
import sys
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = PACKAGE_DIR / "config.json"

if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))


REQUIRED_PATHS = [
    "always_on_runtime.py",
    "config.json",
    "start.bat",
    "setup_api.bat",
    "setup_rest_api.py",
    "setup_database.bat",
    "setup_sql_odbc.py",
    "src",
    "agents",
    "runtime/customer_input",
    "runtime/customer_output",
    "runtime/modula_output",
    "runtime/processed",
    "runtime/errors",
    "runtime/profiles",
    "runtime/sql",
]

REQUIRED_IMPORTS = [
    "src.pipeline.file_processing_pipeline",
    "src.connectors.rest_api_connector",
    "src.connectors.db_connector",
    "agents.openai_field_mapping_agent",
]


def check_path(relative_path: str) -> bool:
    path = PACKAGE_DIR / relative_path
    if path.exists():
        print(f"[OK] Path exists: {relative_path}")
        return True

    print(f"[FAIL] Missing path: {relative_path}")
    return False


def check_import(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        print(f"[OK] Import works: {module_name}")
        return True
    except Exception as error:
        print(f"[FAIL] Import failed: {module_name} -> {error}")
        return False


def check_config() -> bool:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            config = json.load(file)

        print(f"[OK] Config loads: {CONFIG_PATH.name}")
        print(f"     Customer: {config.get('customer_name')}")
        print(f"     Generator version: {config.get('generator_version', 'unknown')}")
        print(f"     REST enabled: {config.get('rest_api', {}).get('enabled')}")
        print(f"     SQL enabled: {config.get('sql', {}).get('enabled')}")
        return True

    except Exception as error:
        print(f"[FAIL] Config check failed: {error}")
        return False


def main() -> None:
    print("=" * 70)
    print("MODULA MIDDLEWARE PACKAGE SELF-TEST")
    print("=" * 70)
    print(f"Package: {PACKAGE_DIR}")
    print()

    checks = []
    checks.append(check_config())

    for relative_path in REQUIRED_PATHS:
        checks.append(check_path(relative_path))

    for module_name in REQUIRED_IMPORTS:
        checks.append(check_import(module_name))

    print()
    print("=" * 70)

    if all(checks):
        print("SELF-TEST PASSED")
        print("The generated package structure and imports look valid.")
        sys.exit(0)

    print("SELF-TEST FAILED")
    print("Review the failed checks above before deploying this package.")
    sys.exit(1)


if __name__ == "__main__":
    main()
