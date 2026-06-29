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
        rest_api = config.get("rest_api", {})
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
