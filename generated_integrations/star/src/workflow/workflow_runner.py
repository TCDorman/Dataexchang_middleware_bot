"""
workflow_runner.py

Runs the full post-transformation workflow for the Modula WMS Data Integration Agent.

This module connects:
1. Validation workflow
2. Decision engine
3. XML export
4. Transaction history logging
"""

from typing import Any, Dict, List

from src.output.xml_export_manager import XmlExportManager
from src.storage.transaction_history import TransactionHistory
from src.workflow.decision_engine import DecisionEngine
from src.workflow.processing_workflow import ProcessingWorkflow


class WorkflowRunner:
    """
    High-level workflow runner for transformed orders.

    This class coordinates validation, decision-making, XML export,
    and transaction logging.
    """

    def __init__(self):
        """
        Initialize the workflow runner and its required components.
        """

        # Handles business rules and data quality checks.
        self.processing_workflow = ProcessingWorkflow()

        # Decides what action should happen after validation.
        self.decision_engine = DecisionEngine()

        # Exports validated orders to XML files.
        self.xml_export_manager = XmlExportManager()

        # Saves each processing run to local transaction history.
        self.transaction_history = TransactionHistory()

    def run(
        self,
        orders: List[Dict[str, Any]],
        metadata: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Run the full workflow for transformed orders.

        Args:
            orders: List of transformed order dictionaries.
            metadata: Optional pipeline metadata such as source file
                      information and order counts.

        Returns:
            Complete workflow result including validation, decision,
            XML export result, and history record.
        """

        # ----------------------------------------------------------
        # Step 1: Run business rules and data quality checks.
        # ----------------------------------------------------------
        workflow_result = self.processing_workflow.process_transformed_orders(
            orders
        )

        # ----------------------------------------------------------
        # Step 2: Decide what should happen next.
        # ----------------------------------------------------------
        decision = self.decision_engine.evaluate(workflow_result)
        workflow_result["decision"] = decision

        # ----------------------------------------------------------
        # Step 3: Only generate XML when approved by the
        # Decision Engine.
        # ----------------------------------------------------------
        if decision["action"] == "generate_xml":
            export_result = self.xml_export_manager.export_orders(
                orders
            )
        else:
            export_result = {
                "status": "skipped",
                "reason": (
                    f"XML export skipped because decision "
                    f"was: {decision['action']}"
                ),
                "output_path": None,
                "orders_exported": 0,
            }

        workflow_result["export_result"] = export_result

        # ----------------------------------------------------------
        # Step 4: Add optional metadata before saving history.
        #
        # This allows source file information to be captured
        # in the audit trail.
        # ----------------------------------------------------------
        if metadata:
            workflow_result.update(metadata)

        # ----------------------------------------------------------
        # Step 5: Save this run to transaction history.
        # ----------------------------------------------------------
        history_record = self.transaction_history.record_run(
            workflow_result
        )

        # ----------------------------------------------------------
        # Step 6: Add the saved history record to the result.
        # ----------------------------------------------------------
        workflow_result["history_record"] = history_record

        return workflow_result