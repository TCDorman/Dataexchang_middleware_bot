import json
from pathlib import Path
from datetime import datetime


AUDIT_LOG_PATH = Path("logs/integration_audit_log.jsonl")


def write_audit_log(
    customer_name: str,
    direction: str,
    input_files: list[str],
    output_file: str,
    status: str,
    validation_errors: list[str] | None = None,
):
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "customer_name": customer_name,
        "direction": direction,
        "input_files": input_files,
        "output_file": output_file,
        "status": status,
        "validation_errors": validation_errors or [],
    }

    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as file:
        file.write(json.dumps(log_entry) + "\n")

    return {
        "status": "success",
        "log_path": str(AUDIT_LOG_PATH),
        "entry": log_entry,
    }


def read_audit_log():
    if not AUDIT_LOG_PATH.exists():
        return []

    entries = []

    with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as file:
        for line in file:
            entries.append(json.loads(line))

    return entries