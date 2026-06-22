"""
run_ford_local_agent.py

Local automation runner for Ford.
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
SUPPORTED_FILE_EXTENSIONS = {".csv", ".json", ".xml"}


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

    logging.info("Logging initialized.")
    logging.info("Log file: %s", log_path)


def load_status(config: dict) -> dict:
    status_path = Path(
        config.get("status_path", Path(__file__).parent / "status.json")
    )

    if not status_path.exists():
        return {
            "customer_name": config.get("customer_name"),
            "status": "not_started",
            "last_run": None,
            "last_success": None,
            "last_error": None,
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
        }

    with open(status_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_status(config: dict, status: dict) -> None:
    status_path = Path(config.get("status_path", Path(__file__).parent / "status.json"))
    status_path.parent.mkdir(parents=True, exist_ok=True)

    status["updated_at"] = datetime.now().isoformat()

    with open(status_path, "w", encoding="utf-8") as file:
        json.dump(status, file, indent=4)


def update_status_starting(config: dict) -> None:
    status = load_status(config)
    status["customer_name"] = config.get("customer_name")
    status["status"] = "running"
    status["last_run"] = datetime.now().isoformat()
    status["last_error"] = None
    status["total_runs"] = status.get("total_runs", 0) + 1

    save_status(config, status)


def update_status_success(config: dict) -> None:
    status = load_status(config)
    status["status"] = "healthy"
    status["last_success"] = datetime.now().isoformat()
    status["last_error"] = None
    status["successful_runs"] = status.get("successful_runs", 0) + 1

    save_status(config, status)


def update_status_error(config: dict, error: Exception) -> None:
    status = load_status(config)
    status["status"] = "error"
    status["last_error"] = str(error)
    status["failed_runs"] = status.get("failed_runs", 0) + 1

    save_status(config, status)


def retry_operation(
    operation_name: str,
    operation,
    attempts: int = 3,
    delay_seconds: int = 5,
):
    last_error = None

    for attempt_number in range(1, attempts + 1):
        try:
            logging.info(
                "Starting operation '%s' attempt %s of %s",
                operation_name,
                attempt_number,
                attempts,
            )

            return operation()

        except Exception as error:
            last_error = error

            logging.warning(
                "Operation '%s' failed on attempt %s of %s: %s",
                operation_name,
                attempt_number,
                attempts,
                error,
            )

            if attempt_number < attempts:
                logging.info(
                    "Retrying operation '%s' in %s seconds...",
                    operation_name,
                    delay_seconds,
                )
                time.sleep(delay_seconds)

    raise last_error


def load_processed_files(config: dict) -> set:
    state_path = Path(config.get("processed_files_state_path", "processed_files.json"))

    if not state_path.exists():
        return set()

    with open(state_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return set(data.get("processed_files", []))


def save_processed_files(config: dict, processed_files: set) -> None:
    state_path = Path(config.get("processed_files_state_path", "processed_files.json"))
    state_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "processed_files": sorted(processed_files),
        "updated_at": datetime.now().isoformat(),
    }

    with open(state_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def archive_processed_file(config: dict, file_path: Path) -> Path:
    archive_folder = Path(
        config.get("processed_files_archive_folder", "processed_files_archive")
    )
    archive_folder.mkdir(parents=True, exist_ok=True)

    archive_path = archive_folder / file_path.name

    if archive_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = archive_folder / f"{file_path.stem}_{timestamp}{file_path.suffix}"

    file_path.rename(archive_path)

    return archive_path


def reset_file_state(config: dict):
    state_path = Path(config.get("processed_files_state_path", "processed_files.json"))

    if state_path.exists():
        state_path.unlink()
        print(f"Deleted processed file state: {state_path}")
    else:
        print(f"No processed file state found at: {state_path}")


def reset_rest_state(config: dict):
    state_path = config.get("processed_state_path")

    if not state_path:
        print("No processed REST state path configured.")
        return

    path = Path(state_path)

    if path.exists():
        path.unlink()
        print(f"Deleted processed REST state file: {path}")
    else:
        print(f"No processed REST state file found at: {path}")


def reset_wms_export_state(config: dict):
    state_path = config.get("processed_wms_exports_state_path")

    if not state_path:
        print("No processed WMS export state path configured.")
        return

    path = Path(state_path)

    if path.exists():
        path.unlink()
        print(f"Deleted processed WMS export state file: {path}")
    else:
        print(f"No processed WMS export state file found at: {path}")


def run_file_once(config: dict):
    input_folder = Path(config["customer_input_folder"])
    input_folder.mkdir(parents=True, exist_ok=True)

    processed_files = load_processed_files(config)
    workflow_manager = IntegrationWorkflowManager()

    files = [
        path
        for path in input_folder.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_FILE_EXTENSIONS
    ]

    if not files:
        logging.info("No customer input files found in %s", input_folder)
        return

    for file_path in files:
        file_key = str(file_path.resolve())

        if file_key in processed_files:
            logging.info("Skipping already processed file: %s", file_path)
            continue

        logging.info("Processing customer input file: %s", file_path)

        result = workflow_manager.run_file_workflow(
            file_path=str(file_path),
            customer_name=config["customer_name"],
            mapping_confirmation_callback=None,
        )

        logging.info("File workflow result:")
        logging.info(json.dumps(result, indent=4))

        if result.get("status") == "success":
            archive_path = archive_processed_file(config, file_path)

            processed_files.add(str(archive_path.resolve()))
            save_processed_files(config, processed_files)

            logging.info("Moved processed file to archive: %s", archive_path)
        else:
            logging.warning("File was not archived because workflow failed.")


def run_rest_api_once(config: dict):
    rest_api = config.get("rest_api", {})
    base_url = rest_api.get("base_url")
    endpoint = rest_api.get("endpoint")
    profile_path = config.get("customer_profile_path")

    if not base_url or not endpoint:
        logging.warning(
            "REST API base_url or endpoint missing. Skipping REST run."
        )
        return

    result = generate_modula_xml_from_rest_api(
        base_url=base_url,
        endpoint=endpoint,
        profile_path=profile_path,
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

    logging.info("REST API to IMP_ORDINI XML result:")
    logging.info(json.dumps(result, indent=4))


def run_wms_export_scan_once(config: dict):
    wms_export_folder = config.get("wms_export_folder")
    customer_output_folder = config.get("customer_output_folder")
    customer_name = config.get("customer_name")

    if not wms_export_folder or not customer_output_folder:
        logging.info("WMS export folder or customer output folder not configured.")
        return

    logging.info("Scanning WMS export folder: %s", wms_export_folder)

    results = scan_wms_export_folder_once(
        watch_folder=wms_export_folder,
        customer_name=customer_name,
        output_folder=customer_output_folder,
        processed_state_path=config.get("processed_wms_exports_state_path"),
    )

    logging.info("WMS export scan result:")
    logging.info(json.dumps(results, indent=4))


def run_once():
    config = load_config()
    setup_logging(config)

    update_status_starting(config)

    try:
        logging.info("Running local agent once for %s", config["customer_name"])

        retry_attempts = int(config.get("retry_attempts", 3))
        retry_delay_seconds = int(config.get("retry_delay_seconds", 5))

        if config.get("source_type") == "rest_api":
            retry_operation(
                operation_name="REST API import",
                operation=lambda: run_rest_api_once(config),
                attempts=retry_attempts,
                delay_seconds=retry_delay_seconds,
            )
        else:
            retry_operation(
                operation_name="customer file import",
                operation=lambda: run_file_once(config),
                attempts=retry_attempts,
                delay_seconds=retry_delay_seconds,
            )

        retry_operation(
            operation_name="WMS export scan",
            operation=lambda: run_wms_export_scan_once(config),
            attempts=retry_attempts,
            delay_seconds=retry_delay_seconds,
        )

        update_status_success(config)
        logging.info("Run once complete.")

    except Exception as error:
        update_status_error(config, error)
        logging.exception("Local agent run failed.")


def run_forever(poll_seconds: int = 5):
    config = load_config()
    setup_logging(config)

    logging.info("Starting local agent for %s", config["customer_name"])
    logging.info(json.dumps(config, indent=4))

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

    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one scan cycle and exit.",
    )

    parser.add_argument(
        "--watch",
        action="store_true",
        help="Continuously watch folders.",
    )

    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=5,
        help="Polling interval for watch mode.",
    )

    parser.add_argument(
        "--reset-rest-state",
        action="store_true",
        help="Delete processed REST record state so records can be reprocessed.",
    )

    parser.add_argument(
        "--reset-file-state",
        action="store_true",
        help="Delete processed file state so files can be reprocessed.",
    )

    parser.add_argument(
        "--reset-wms-export-state",
        action="store_true",
        help="Delete processed WMS export state so export files can be reprocessed.",
    )

    args = parser.parse_args()
    config = load_config()

    if args.reset_rest_state:
        reset_rest_state(config)
        return

    if args.reset_file_state:
        reset_file_state(config)
        return

    if args.reset_wms_export_state:
        reset_wms_export_state(config)
        return

    if args.once:
        run_once()
        return

    if args.watch:
        run_forever(poll_seconds=args.poll_seconds)
        return

    run_forever(poll_seconds=args.poll_seconds)


if __name__ == "__main__":
    main()
