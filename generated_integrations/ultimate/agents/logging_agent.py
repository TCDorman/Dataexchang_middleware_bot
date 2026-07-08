from pathlib import Path
from datetime import datetime


# ==================================================
# Log Directory Setup
# ==================================================
def get_log_directory():
    """
    Ensure the log directory exists and return it.
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    return log_dir


# ==================================================
# Write Log Entry
# ==================================================
def write_log(
    customer_name: str,
    status: str,
    files: list,
    message: str,
):
    """
    Write a processing event to the daily log file.
    """

    log_dir = get_log_directory()

    log_file = (
        log_dir
        / f"integration_{datetime.now():%Y_%m_%d}.log"
    )

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    log_entry = (
        f"\n{'=' * 60}\n"
        f"Timestamp: {timestamp}\n"
        f"Customer: {customer_name}\n"
        f"Status: {status}\n"
        f"Files:\n"
    )

    for file in files:
        log_entry += f"  - {file}\n"

    log_entry += f"\nMessage:\n{message}\n"

    with open(
        log_file,
        "a",
        encoding="utf-8",
    ) as file:
        file.write(log_entry)