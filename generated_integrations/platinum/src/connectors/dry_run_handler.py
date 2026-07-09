"""
dry_run_handler.py

Provides dry-run support for REST pull and push integrations.
"""

from copy import deepcopy
from datetime import datetime
from typing import Any


class DryRunHandler:
    """
    Simulates integration operations without performing external actions.
    """

    def create_pull_preview(
        self,
        records: Any,
        source_url: str,
    ) -> dict:
        preview = deepcopy(records)

        return {
            "status": "dry_run",
            "operation": "pull",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "source_url": source_url,
            "record_count": self._count_records(preview),
            "preview": preview,
        }

    def create_push_preview(
        self,
        payload: Any,
        destination_url: str,
        method: str = "POST",
    ) -> dict:
        preview = deepcopy(payload)

        return {
            "status": "dry_run",
            "operation": "push",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "destination_url": destination_url,
            "http_method": method.upper(),
            "record_count": self._count_records(preview),
            "preview": preview,
        }

    @staticmethod
    def _count_records(data: Any) -> int:
        if isinstance(data, list):
            return len(data)

        if isinstance(data, dict):
            return 1

        return 0