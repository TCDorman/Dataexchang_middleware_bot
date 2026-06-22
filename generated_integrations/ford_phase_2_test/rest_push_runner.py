"""
rest_push_runner.py

Generated REST push script for Ford Phase 2 Test.
"""

import argparse
import csv
import json
import logging
from datetime import datetime
from pathlib import Path

import requests


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


def setup_logger(config: dict):
    log_path = Path(config.get("log_path", "logs/rest_push_runner.log"))
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("rest_push_runner")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

    return logger


def log_event(logger, event_type: str, message: str, level: str = "INFO", **details):
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


def save_failed_record(config: dict, record: dict, reason: str, metadata: dict | None = None) -> str:
    folder = Path(config.get("dead_letter_folder", "data/dead_letter"))
    folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_path = folder / f"failed_record_{timestamp}.json"

    payload = {
        "timestamp": timestamp,
        "source": "rest_push_runner",
        "reason": reason,
        "record": record,
        "metadata": metadata or {},
    }

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=4, default=str)

    return str(output_path)


def load_source_records(source_path: str) -> list[dict]:
    path = Path(source_path)

    if path.suffix.lower() == ".json":
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            return data.get("records", [data])

    if path.suffix.lower() == ".csv":
        with open(path, "r", encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))

    raise ValueError(f"Unsupported source file type: {path.suffix}")


def build_headers(config: dict) -> dict:
    headers = config.get("headers", {}).copy()
    headers.setdefault("Content-Type", "application/json")

    api_key = config.get("api_key")
    api_key_header = config.get("api_key_header", "Authorization")
    bearer_token = config.get("bearer_token", True)

    if api_key:
        headers[api_key_header] = f"Bearer {api_key}" if bearer_token else api_key

    return headers


def parse_target_path(path: str) -> list[dict]:
    parts = []

    for raw_part in path.split("."):
        if "[" in raw_part and raw_part.endswith("]"):
            key = raw_part.split("[")[0]
            index_text = raw_part.split("[")[1].replace("]", "")
            parts.append({"key": key, "array_index": int(index_text)})
        else:
            parts.append({"key": raw_part, "array_index": None})

    return parts


def set_nested_value(body: dict, path: str, value) -> None:
    parts = parse_target_path(path)
    current = body

    for index, part in enumerate(parts):
        is_last = index == len(parts) - 1
        key = part["key"]
        array_index = part["array_index"]

        if array_index is None:
            if is_last:
                current[key] = value
            else:
                next_part = parts[index + 1]
                should_be_list = next_part["array_index"] is not None

                if key not in current:
                    current[key] = [] if should_be_list else {}

                current = current[key]
        else:
            if key not in current:
                current[key] = []

            while len(current[key]) <= array_index:
                current[key].append({})

            if is_last:
                current[key][array_index] = value
            else:
                current = current[key][array_index]


def build_body(source_record: dict, field_mapping: dict) -> dict:
    body = {}

    for source_field, target_path in field_mapping.items():
        value = source_record.get(source_field)

        if value is None:
            continue

        set_nested_value(body, target_path, value)

    return body


def push_once(config: dict, dry_run: bool = False) -> dict:
    logger = setup_logger(config)

    url = config["url"]
    source_path = config["source_path"]
    field_mapping = config["field_mapping"]
    method = config.get("method", "POST").upper()
    timeout = config.get("timeout", 30)

    records = load_source_records(source_path)
    headers = build_headers(config)

    log_event(
        logger,
        "PUSH_START",
        "REST push run started.",
        customer_name="Ford Phase 2 Test",
        url=url,
        method=method,
        record_count=len(records),
        dry_run=dry_run,
    )

    successes = []
    failures = []
    dry_run_payloads = []

    for index, record in enumerate(records, start=1):
        body = build_body(record, field_mapping)

        if dry_run:
            dry_run_payloads.append({
                "record_number": index,
                "request_body": body,
            })
            continue

        try:
            if method == "PUT":
                response = requests.put(url, headers=headers, json=body, timeout=timeout)
            else:
                response = requests.post(url, headers=headers, json=body, timeout=timeout)

            if response.status_code in (200, 201, 202, 204):
                successes.append({
                    "record_number": index,
                    "status_code": response.status_code,
                })

                log_event(
                    logger,
                    "PUSH_SENT",
                    "Record pushed successfully.",
                    record_number=index,
                    status_code=response.status_code,
                )
            else:
                failure = {
                    "record_number": index,
                    "status_code": response.status_code,
                    "request_body": body,
                    "response": response.text[:1000],
                }

                dlq_path = save_failed_record(
                    config=config,
                    record=record,
                    reason=f"HTTP {response.status_code}",
                    metadata=failure,
                )

                failure["dead_letter_path"] = dlq_path
                failures.append(failure)

                log_event(
                    logger,
                    "PUSH_FAILED",
                    "Record push failed.",
                    level="ERROR",
                    record_number=index,
                    status_code=response.status_code,
                    dead_letter_path=dlq_path,
                )

        except Exception as error:
            failure = {
                "record_number": index,
                "request_body": body,
                "error": str(error),
            }

            dlq_path = save_failed_record(
                config=config,
                record=record,
                reason=str(error),
                metadata=failure,
            )

            failure["dead_letter_path"] = dlq_path
            failures.append(failure)

            log_event(
                logger,
                "RECORD_FAILED",
                "Exception occurred while pushing record.",
                level="ERROR",
                record_number=index,
                error=str(error),
                dead_letter_path=dlq_path,
            )

    if dry_run:
        result = {
            "status": "dry_run",
            "source_type": "rest_api",
            "customer_name": "Ford Phase 2 Test",
            "url": url,
            "method": method,
            "records_loaded": len(records),
            "records_previewed": len(dry_run_payloads),
            "payload_preview": dry_run_payloads,
        }

        log_event(logger, "PUSH_COMPLETE", "Dry-run push completed.", **result)
        return result

    result = {
        "status": "success" if not failures else "partial_failure",
        "source_type": "rest_api",
        "customer_name": "Ford Phase 2 Test",
        "records_loaded": len(records),
        "records_pushed": len(successes),
        "records_failed": len(failures),
        "successes": successes,
        "failures": failures,
    }

    log_event(logger, "PUSH_COMPLETE", "REST push run completed.", **result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    config = load_config(args.config)

    result = push_once(config, dry_run=args.dry_run)
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
