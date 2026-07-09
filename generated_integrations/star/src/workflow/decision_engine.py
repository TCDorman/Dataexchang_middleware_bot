"""
decision_engine.py

Determines what action the integration agent should take after
workflow processing has completed.

The Decision Engine evaluates workflow results and chooses the
next step in the processing pipeline.

Examples:
    - Generate XML
    - Send for manual review
    - Stop processing
    - Archive results
"""


from typing import Any, Dict


class DecisionEngine:
    """
    Evaluates workflow results and determines the next action.
    """

    def evaluate(self, workflow_result: Dict[str, Any]) -> Dict[str, str]:
        """
        Determine what action should be taken after processing.

        Args:
            workflow_result: Result returned by ProcessingWorkflow.

        Returns:
            Dictionary containing:
                - action
                - reason
        """

        validation_report = workflow_result["validation_report"]

        quality_score = validation_report["quality_score"]

        data_quality_errors = validation_report["data_quality_errors"]

        ready_for_xml = workflow_result["ready_for_xml"]

        # ---------------------------------------------------------
        # Rule 1:
        # If validation failed, processing must stop.
        # ---------------------------------------------------------
        if not ready_for_xml:
            return {
                "action": "stop_processing",
                "reason": "Validation errors prevent XML generation.",
            }

        # ---------------------------------------------------------
        # Rule 2:
        # If the data quality score is low, send for review.
        # ---------------------------------------------------------
        if quality_score < 70:
            return {
                "action": "manual_review",
                "reason": f"Quality score is below threshold ({quality_score}%).",
            }

        # ---------------------------------------------------------
        # Rule 3:
        # If data quality errors exist, require review.
        # ---------------------------------------------------------
        if data_quality_errors:
            return {
                "action": "manual_review",
                "reason": "Data quality issues require review.",
            }

        # ---------------------------------------------------------
        # Rule 4:
        # Everything looks good.
        # ---------------------------------------------------------
        return {
            "action": "generate_xml",
            "reason": "Validation passed successfully.",
        }