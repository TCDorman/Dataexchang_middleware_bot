"""
transaction_history.py

Local transaction history storage for the Modula WMS Data Integration Agent.

This module records all processing activity including:

- Successful runs
- Failed runs
- Validation results
- XML exports
- Pipeline errors

This creates an audit trail that can later be used for reporting,
troubleshooting, and monitoring.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class TransactionHistory:
    """
    Stores and retrieves workflow processing history.
    """

    def __init__(self, history_path: str = "data/history/transactions.json"):
        """
        Initialize the transaction history store.

        Args:
            history_path: File path where transaction history is saved.
        """

        self.history_path = Path(history_path)

        # Create history folder if needed.
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

        # Create history file if it does not exist.
        if not self.history_path.exists():
            self.history_path.write_text(
                "[]",
                encoding="utf-8",
            )

    def record_run(
        self,
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Save a workflow result to history.

        Args:
            result: Workflow result dictionary.

        Returns:
            Saved history record.
        """

        history = self.get_history()

        # ----------------------------------------------------------
        # Error Record
        # ----------------------------------------------------------
        if result.get("status") == "error":

            record = {
                "timestamp": datetime.now().isoformat(
                    timespec="seconds"
                ),
                "status": "error",
                "source_file": result.get("source_file"),
                "error_message": result.get("error_message"),
                "decision_action": (
                    result.get("decision", {})
                    .get("action")
                ),
                "decision_reason": (
                    result.get("decision", {})
                    .get("reason")
                ),
            }

        # ----------------------------------------------------------
        # Success Record
        # ----------------------------------------------------------
        else:

            record = {
                "timestamp": datetime.now().isoformat(
                    timespec="seconds"
                ),

                "status": result.get("status"),

                "orders_processed": result.get(
                    "orders_processed"
                ),

                "ready_for_xml": result.get(
                    "ready_for_xml"
                ),

                "quality_score": (
                    result.get(
                        "validation_report",
                        {},
                    ).get("quality_score")
                ),

                "decision_action": (
                    result.get("decision", {})
                    .get("action")
                ),

                "decision_reason": (
                    result.get("decision", {})
                    .get("reason")
                ),

                "export_status": (
                    result.get("export_result", {})
                    .get("status")
                ),

                "output_path": (
                    result.get("export_result", {})
                    .get("output_path")
                ),

                "orders_exported": (
                    result.get("export_result", {})
                    .get("orders_exported")
                ),

                "source_file": result.get(
                    "source_file"
                ),

                "orders_loaded": result.get(
                    "orders_loaded"
                ),

                "parser_used": result.get(
                    "parser_used"
                ),

                "profile_used": result.get(
                    "profile_used"
                ),
            }

        history.append(record)

        self.history_path.write_text(
            json.dumps(history, indent=4),
            encoding="utf-8",
        )

        return record

    def get_history(self) -> List[Dict[str, Any]]:
        """
        Load all transaction history.

        Returns:
            List of history records.
        """

        try:
            return json.loads(
                self.history_path.read_text(
                    encoding="utf-8"
                )
            )

        except json.JSONDecodeError:
            return []