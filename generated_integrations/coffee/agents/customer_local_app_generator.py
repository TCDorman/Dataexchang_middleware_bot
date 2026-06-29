"""
customer_local_app_generator.py

Generates a customer-specific local automation runner.
"""

import json
from pathlib import Path
from typing import Dict

from src.generators.always_on_runtime_generator import AlwaysOnRuntimeGenerator


def get_safe_customer_name(customer_name: str) -> str:
    return customer_name.strip().lower().replace(" ", "_")


def write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        file.write(content)


def write_json_file(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def generate_customer_local_app(
    customer_name: str,
    customer_profile_path: str,
    customer_input_folder: str = "data/customer_input",
    ordini_import_folder: str = "data/wms_imports/ordini",
    articoli_import_folder: str = "data/wms_imports/articoli",
    wms_export_folder: str = "data/wms_exports",
    customer_output_folder: str = "data/customer_exports",
    source_type: str = "file",
    rest_api_base_url: str | None = None,
    rest_api_endpoint: str | None = None,
    rest_api_auth_type: str = "none",
    rest_api_key: str | None = None,
    rest_api_key_header: str = "Authorization",
    rest_api_bearer_token: str | None = None,
    rest_api_username: str | None = None,
    rest_api_password: str | None = None,
    rest_api_pagination_strategy: str = "none",
    rest_api_results_key: str | None = None,
    rest_api_max_pages: int = 10,
) -> Dict:
    safe_customer_name = get_safe_customer_name(customer_name)

    package_folder = Path("generated_integrations") / safe_customer_name
    package_folder.mkdir(parents=True, exist_ok=True)

    runner_path = package_folder / f"run_{safe_customer_name}_local_agent.py"
    config_path = package_folder / "local_agent_config.json"
    readme_path = package_folder / "README_LOCAL_AGENT.txt"
    logs_folder = package_folder / "logs"
    archive_folder = package_folder / "processed_files_archive"
    install_startup_task_path = package_folder / "install_startup_task.bat"
    uninstall_startup_task_path = package_folder / "uninstall_startup_task.bat"

    runtime_folder = package_folder / "runtime"
    runtime_input_folder = runtime_folder / "customer_input"
    runtime_output_folder = runtime_folder / "modula_output"
    runtime_processed_folder = runtime_folder / "processed"
    runtime_errors_folder = runtime_folder / "errors"
    runtime_profiles_folder = runtime_folder / "profiles"

    for folder in [
        logs_folder,
        archive_folder,
        runtime_input_folder,
        runtime_output_folder,
        runtime_processed_folder,
        runtime_errors_folder,
        runtime_profiles_folder,
    ]:
        folder.mkdir(parents=True, exist_ok=True)

    config = {
        "customer_name": customer_name,
        "safe_customer_name": safe_customer_name,
        "customer_profile_path": customer_profile_path,
        "customer_input_folder": customer_input_folder,
        "ordini_import_folder": ordini_import_folder,
        "articoli_import_folder": articoli_import_folder,
        "wms_export_folder": wms_export_folder,
        "customer_output_folder": customer_output_folder,
        "logs_folder": str(logs_folder),
        "processed_state_path": str(package_folder / "processed_rest_records.json"),
        "processed_files_state_path": str(package_folder / "processed_files.json"),
        "processed_wms_exports_state_path": str(
            package_folder / "processed_wms_exports.json"
        ),
        "processed_files_archive_folder": str(archive_folder),
        "status_path": str(package_folder / "status.json"),
        "retry_attempts": 3,
        "retry_delay_seconds": 5,
        "mode": "local_customer_runner",
        "wms_runtime": "FolderWMSAdapter",
        "source_type": source_type,
        "runtime": {
            "runtime_folder": str(runtime_folder),
            "customer_input_folder": str(runtime_input_folder),
            "modula_output_folder": str(runtime_output_folder),
            "processed_folder": str(runtime_processed_folder),
            "errors_folder": str(runtime_errors_folder),
            "profiles_folder": str(runtime_profiles_folder),
            "output_format": "modula_wms_xml",
        },
        "rest_api": {
            "base_url": rest_api_base_url,
            "endpoint": rest_api_endpoint,
            "auth_type": rest_api_auth_type,
            "api_key": rest_api_key,
            "api_key_header": rest_api_key_header,
            "bearer_token": rest_api_bearer_token,
            "username": rest_api_username,
            "password": rest_api_password,
            "pagination_strategy": rest_api_pagination_strategy,
            "results_key": rest_api_results_key,
            "max_pages": rest_api_max_pages,
        },
    }

    runner_code = f'''"""
run_{safe_customer_name}_local_agent.py

Local automation runner for {customer_name}.
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from agents.integration_workflow_manager import IntegrationWorkflowManager
from agents.rest_to_modula_xml_agent import generate_modula_xml_from_rest_api
from agents.agents.export_ordini_monitor_agent import scan_wms_export_folder_once


CONFIG_PATH = Path(__file__).parent / "local_agent_config.json"
SUPPORTED_FILE_EXTENSIONS = {{".csv", ".json", ".xml"}}


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def setup_logging(config: dict):
    logs_folder = Path(config.get("logs_folder", Path(__file__).parent / "logs"))
    logs_folder.mkdir(parents=True, exist_ok=True)

    log_path = logs_folder / "local_agent.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def run_once():
    config = load_config()
    setup_logging(config)

    logging.info("Running local agent once for %s", config["customer_name"])
    workflow_manager = IntegrationWorkflowManager()

    input_folder = Path(config["customer_input_folder"])
    input_folder.mkdir(parents=True, exist_ok=True)

    files = [
        path
        for path in input_folder.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_FILE_EXTENSIONS
    ]

    if config.get("source_type") == "rest_api":
        rest_api = config.get("rest_api", {{}})
        result = generate_modula_xml_from_rest_api(
            base_url=rest_api.get("base_url"),
            endpoint=rest_api.get("endpoint"),
            profile_path=config.get("customer_profile_path"),
            output_folder=config["ordini_import_folder"],
            auth_type=rest_api.get("auth_type", "none"),
            api_key=rest_api.get("api_key"),
            api_key_header=rest_api.get("api_key_header", "Authorization"),
            bearer_token=rest_api.get("bearer_token"),
            username=rest_api.get("username"),
            password=rest_api.get("password"),
            pagination_strategy=rest_api.get("pagination_strategy", "none"),
            results_key=rest_api.get("results_key"),
            max_pages=rest_api.get("max_pages", 10),
            processed_state_path=config.get("processed_state_path"),
        )
        logging.info(json.dumps(result, indent=4))
        return

    for file_path in files:
        result = workflow_manager.run_file_workflow(
            file_path=str(file_path),
            customer_name=config["customer_name"],
            mapping_confirmation_callback=None,
        )

        logging.info(json.dumps(result, indent=4))


def run_forever(poll_seconds: int = 5):
    try:
        while True:
            run_once()
            time.sleep(poll_seconds)
    except KeyboardInterrupt:
        logging.info("Local agent stopped by user.")


def main():
    parser = argparse.ArgumentParser(
        description="Customer-specific Modula WMS local automation agent."
    )

    parser.add_argument("--once", action="store_true")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=5)

    args = parser.parse_args()

    if args.once:
        run_once()
        return

    run_forever(poll_seconds=args.poll_seconds)


if __name__ == "__main__":
    main()
'''

    always_on_runtime_generator = AlwaysOnRuntimeGenerator()
    always_on_runtime_result = always_on_runtime_generator.generate(
        customer_name=customer_name,
        output_folder=str(package_folder),
        script_name="always_on_runtime.py",
    )

    runtime_launcher_path = package_folder / "start_runtime.bat"

    runtime_launcher = f"""@echo off
cd /d "%~dp0"

echo ==================================================
echo MODULA MIDDLEWARE RUNTIME
echo Customer: {customer_name}
echo ==================================================
echo.
echo Watching folder:
echo runtime\\customer_input
echo.
echo Converted Modula XML output:
echo runtime\\modula_output
echo.

python always_on_runtime.py

pause
"""

    runtime_readme_path = package_folder / "README_RUNTIME.txt"

    runtime_readme = f"""
MODULA MIDDLEWARE RUNTIME

Customer:
{customer_name}

Purpose:
This package runs a local always-on middleware runtime.

How to use:

1. Put customer CSV files into:

   runtime\\customer_input

2. Start the runtime by double-clicking:

   start_runtime.bat

3. Converted Modula WMS XML files will appear in:

   runtime\\modula_output

4. Successfully processed files move to:

   runtime\\processed

5. Failed files move to:

   runtime\\errors

6. Saved mapping profiles are stored in:

   runtime\\profiles

Output Format:
Modula WMS XML using SYSTORE / IMP_ORDINI / IMP_ORDINI_RIGHE.

Mapping:
The first time a new customer file format is processed, the runtime asks the AI
to suggest field mappings and then asks the user to confirm them.

After confirmation, the mapping is saved and reused automatically for future files.

Required CSV fields can vary by customer, but the runtime maps them to:

- order_id
- customer_name
- item
- quantity

Example input CSV:

ORDER_NUMBER,CUSTOMER,PART_NUMBER,ORDER_QTY
ORDER11,ORDER 11,ITEM01,2
ORDER11,ORDER 11,ITEM02,2
ORDER12,ORDER 12,ITEM03,2

Expected XML output will be written to:

runtime\\modula_output
"""

    install_startup_task_script = f'''@echo off
set TASK_NAME=Modula_{safe_customer_name}_Runtime

echo Installing startup task for {customer_name} runtime...
echo.

schtasks /Create ^
    /TN "%TASK_NAME%" ^
    /SC ONLOGON ^
    /RL HIGHEST ^
    /TR "\\"%~dp0start_runtime.bat\\"" ^
    /F

echo.
echo Startup task installed successfully.
echo The runtime will start automatically when this Windows user logs in.
echo.
pause
'''

    uninstall_startup_task_script = f'''@echo off
set TASK_NAME=Modula_{safe_customer_name}_Runtime

echo Removing startup task for {customer_name} runtime...
echo.

schtasks /Delete /TN "%TASK_NAME%" /F

echo.
echo Startup task removed successfully.
echo.
pause
'''

    readme_text = f"""
LOCAL CUSTOMER AGENT PACKAGE

Customer:
{customer_name}

Source Type:
{source_type}

Main Runtime:
always_on_runtime.py

Launcher:
start_runtime.bat

Runtime Input Folder:
runtime\\customer_input

Runtime Modula XML Output Folder:
runtime\\modula_output

Runtime Processed Folder:
runtime\\processed

Runtime Error Folder:
runtime\\errors

Runtime Profiles Folder:
runtime\\profiles

Customer Profile:
{customer_profile_path}

Legacy Runner:
{runner_path.name}

Legacy Run Once:
python {runner_path.name} --once

Legacy Watch:
python {runner_path.name} --watch

Install automatic startup task:
Double-click install_startup_task.bat

Uninstall automatic startup task:
Double-click uninstall_startup_task.bat

Logs:
{logs_folder}
"""

    write_json_file(config_path, config)
    write_text_file(runner_path, runner_code)
    write_text_file(runtime_launcher_path, runtime_launcher)
    write_text_file(runtime_readme_path, runtime_readme.strip())
    write_text_file(install_startup_task_path, install_startup_task_script)
    write_text_file(uninstall_startup_task_path, uninstall_startup_task_script)
    write_text_file(readme_path, readme_text.strip())

    return {
        "status": "success",
        "customer_name": customer_name,
        "package_folder": str(package_folder),
        "runner_path": str(runner_path),
        "config_path": str(config_path),
        "readme_path": str(readme_path),
        "logs_folder": str(logs_folder),
        "install_startup_task_path": str(install_startup_task_path),
        "uninstall_startup_task_path": str(uninstall_startup_task_path),
        "runtime_launcher_path": str(runtime_launcher_path),
        "runtime_readme_path": str(runtime_readme_path),
        "runtime_folder": str(runtime_folder),
        "source_type": source_type,
        "always_on_runtime_path": always_on_runtime_result["script_path"],
    }