"""
dead_letter_queue.py

Stores failed integration records for later review or replay.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class DeadLetterQueue:
    """
    Writes failed records to timestamped JSON files.
    """

    def __init__(
        self,
        output_folder: str = "data/dead_letter",
    ):
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)

    def save_failed_record(
        self,
        record: dict,
        reason: str,
        source: str = "unknown",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        payload = {
            "timestamp": timestamp,
            "source": source,
            "reason": reason,
            "record": record,
            "metadata": metadata or {},
        }

        output_path = self.output_folder / f"failed_record_{timestamp}.json"

        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(payload, file, indent=4, default=str)

        return str(output_path)

    def save_failed_batch(
        self,
        records: list[dict],
        reason: str,
        source: str = "unknown",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        payload = {
            "timestamp": timestamp,
            "source": source,
            "reason": reason,
            "record_count": len(records),
            "records": records,
            "metadata": metadata or {},
        }

        output_path = self.output_folder / f"failed_batch_{timestamp}.json"

        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(payload, file, indent=4, default=str)

        return str(output_path)