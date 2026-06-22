"""
run_demo_rest_customer_local_agent.py

Local automation runner for Demo REST Customer.
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from agents.rest_to_modula_xml_agent import generate_modula_xml_from_rest_api


CONFIG_PATH = Path(__file__).parent / "local_agent_config.json"


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
    )

    logging.info("REST API to IMP_ORDINI XML result:")
    logging.info(json.dumps(result, indent=4))


def run_once():
    config = load_config()
    setup_logging(config)

    logging.info("Running local agent once for %s", config["customer_name"])

    if config.get("source_type") == "rest_api":
        run_rest_api_once(config)
        logging.info("Run once complete.")
        return

    logging.info("File-based local runner mode is configured.")


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

    args = parser.parse_args()

    if args.once:
        run_once()
        return

    if args.watch:
        run_forever(poll_seconds=args.poll_seconds)
        return

    run_forever(poll_seconds=args.poll_seconds)


if __name__ == "__main__":
    main()
