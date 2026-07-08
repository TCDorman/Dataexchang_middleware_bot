"""
integration_execution_orchestrator.py

Top-level execution orchestrator for the AI middleware implementation assistant.

This class bridges:
1. AutoIntegrationWorkflow planning output
2. Available discovered/customer inputs
3. AutoPackageGenerationWorkflow execution

Version 1 does not discover inputs automatically yet.
It accepts discovered_inputs and passes them into the package generation workflow.
"""

from typing import Any

from agents.auto_package_generation_workflow import (
    AutoPackageGenerationWorkflow,
)


class IntegrationExecutionOrchestrator:
    """
    Executes package generation from an auto integration workflow result.
    """

    def __init__(self):
        self.package_generation_workflow = AutoPackageGenerationWorkflow()

    def execute(
        self,
        auto_workflow_result: dict[str, Any],
        discovered_inputs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        discovered_inputs = discovered_inputs or {}

        if auto_workflow_result.get("status") != "success":
            return {
                "status": "error",
                "message": "Auto workflow result was not successful.",
                "auto_workflow_status": auto_workflow_result.get("status"),
                "auto_workflow_result": auto_workflow_result,
            }

        generation_plan = auto_workflow_result.get("generation_plan")

        if not generation_plan:
            return {
                "status": "error",
                "message": "Auto workflow result does not contain a generation_plan.",
                "auto_workflow_result": auto_workflow_result,
            }

        generation_result = self.package_generation_workflow.run_generation_plan(
            generation_plan=generation_plan,
            generation_inputs=discovered_inputs,
        )

        return {
            "status": "success",
            "workflow": "integration_execution_orchestrator",
            "detected_integration_type": auto_workflow_result.get(
                "detected_integration_type",
            ),
            "package_generation_ready": auto_workflow_result.get(
                "package_generation_ready",
            ),
            "analysis": auto_workflow_result.get("analysis"),
            "blueprint": auto_workflow_result.get("blueprint"),
            "package_recommendation": auto_workflow_result.get(
                "package_recommendation",
            ),
            "generation_plan": generation_plan,
            "generation_result": generation_result,
            "execution_summary": self._build_execution_summary(
                generation_result,
            ),
        }

    def _build_execution_summary(
        self,
        generation_result: dict[str, Any],
    ) -> dict[str, Any]:
        summary = generation_result.get("summary", {})

        return {
            "generated_count": summary.get("generated_count", 0),
            "skipped_count": summary.get("skipped_count", 0),
            "failed_count": summary.get("failed_count", 0),
            "next_step": generation_result.get("next_step"),
        }