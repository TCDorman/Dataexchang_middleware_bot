"""
rest_pull_runner.py

Generated REST pull script for Ford Auto REST.
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import requests


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


def setup_logger(config: dict):
    log_path = Path(config.get("log_path", "logs/rest_pull_runner.log"))
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("rest_pull_runner")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

    return logger


def log_event(
    logger,
    event_type: str,
    message: str,
    level: str = "INFO",
    **details,
):
    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "event_type": event_type,
        "level": level,
        "message": message,
        "details": details,
    }

    line = json.dumps(record, default=str)

    if level == "ERROR":
        logger.error(line)
    elif level == "WARNING":
        logger.warning(line)
    else:
        logger.info(line)


def build_headers(config: dict) -> dict:
    headers = config.get("headers", {}).copy()

    api_key = config.get("api_key")
    api_key_header = config.get("api_key_header", "Authorization")
    bearer_token = config.get("bearer_token", True)

    if api_key:
        headers[api_key_header] = f"Bearer {api_key}" if bearer_token else api_key

    return headers


def pull_once(config: dict, dry_run: bool = False) -> dict:
    logger = setup_logger(config)

    url = config["url"]
    params = config.get("params", {})
    timeout = config.get("timeout", 30)

    log_event(
        logger,
        "POLL_START",
        "REST pull run started.",
        customer_name="Ford Auto REST",
        url=url,
        dry_run=dry_run,
    )

    try:
        response = requests.get(
            url,
            headers=build_headers(config),
            params=params,
            timeout=timeout,
        )

        response.raise_for_status()

        try:
            data = response.json()
        except ValueError:
            log_event(
                logger,
                "POLL_FAILED",
                "API response was not valid JSON.",
                level="ERROR",
                status_code=response.status_code,
                raw_response=response.text[:1000],
            )

            return {
                "status": "error",
                "source_type": "rest_api",
                "customer_name": "Ford Auto REST",
                "message": "API response was not valid JSON.",
                "status_code": response.status_code,
                "raw_response": response.text[:2000],
            }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        result = {
            "status": "dry_run" if dry_run else "success",
            "source_type": "rest_api",
            "customer_name": "Ford Auto REST",
            "url": url,
            "status_code": response.status_code,
            "pulled_at": timestamp,
            "data": data,
        }

        if dry_run:
            log_event(
                logger,
                "POLL_COMPLETE",
                "Dry-run pull completed.",
                status=result["status"],
                status_code=response.status_code,
            )

            return result

        output_folder = Path(config.get("output_folder", "data/rest_pull_output"))
        output_folder.mkdir(parents=True, exist_ok=True)

        output_path = output_folder / f"rest_pull_{timestamp}.json"

        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(result, file, indent=4)

        result["output_path"] = str(output_path)

        log_event(
            logger,
            "POLL_COMPLETE",
            "REST pull run completed.",
            status=result["status"],
            status_code=response.status_code,
            output_path=str(output_path),
        )

        return result

    except Exception as error:
        log_event(
            logger,
            "POLL_FAILED",
            "REST pull run failed.",
            level="ERROR",
            error=str(error),
        )

        return {
            "status": "error",
            "source_type": "rest_api",
            "customer_name": "Ford Auto REST",
            "message": "REST pull run failed.",
            "url": url,
            "error": str(error),
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    config = load_config(args.config)

    result = pull_once(config, dry_run=args.dry_run)
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
