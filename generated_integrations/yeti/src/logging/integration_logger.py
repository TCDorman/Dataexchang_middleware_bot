"""
integration_logger.py

Shared structured logging utility for generated integrations.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any


class IntegrationLogger:
    """
    Writes structured JSON log events for integration runs.
    """

    def __init__(
        self,
        log_file_path: str = "logs/integration.log",
        logger_name: str = "modula_integration",
    ):
        self.log_file_path = Path(log_file_path)
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()

        file_handler = logging.FileHandler(
            self.log_file_path,
            encoding="utf-8",
        )

        file_handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(file_handler)

    def log_event(
        self,
        event_type: str,
        message: str,
        level: str = "INFO",
        **details: Any,
    ) -> None:
        log_record = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "event_type": event_type,
            "level": level.upper(),
            "message": message,
            "details": details,
        }

        log_line = json.dumps(log_record, default=str)

        if level.upper() == "ERROR":
            self.logger.error(log_line)
        elif level.upper() == "WARNING":
            self.logger.warning(log_line)
        else:
            self.logger.info(log_line)


# Standard event names
POLL_START = "POLL_START"
POLL_COMPLETE = "POLL_COMPLETE"
POLL_PAGE = "POLL_PAGE"

PUSH_START = "PUSH_START"
PUSH_COMPLETE = "PUSH_COMPLETE"
PUSH_SENT = "PUSH_SENT"
PUSH_FAILED = "PUSH_FAILED"

RATE_LIMITED = "RATE_LIMITED"
TOKEN_REFRESHED = "TOKEN_REFRESHED"
RECORD_PROCESSED = "RECORD_PROCESSED"
RECORD_FAILED = "RECORD_FAILED"