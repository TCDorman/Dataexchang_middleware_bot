"""
package_generation_planner.py

Converts package recommendations into a package generation execution plan.

This agent does not generate files. It determines which generation workflows
should run and what inputs are required before they can run.
"""

from typing import Any


class PackageGenerationPlanner:
    """
    Builds an execution plan from package recommendations.
    """

    def build_plan(
        self,
        package_recommendation: dict[str, Any],
    ) -> dict[str, Any]:
        recommendations = package_recommendation.get(
            "recommended_packages",
            [],
        )

        execution_plan = []

        for index, recommendation in enumerate(recommendations, start=1):
            execution_plan.append(
                self._build_plan_step(
                    step=index,
                    recommendation=recommendation,
                )
            )

        return {
            "status": "success",
            "customer_name": package_recommendation.get(
                "customer_name",
                "unknown_customer",
            ),
            "integration_type": package_recommendation.get(
                "integration_type",
                "unclear",
            ),
            "execution_plan": execution_plan,
            "ready_to_execute": all(
                step.get("ready_to_execute", False)
                for step in execution_plan
            ),
            "next_step": self._build_next_step(execution_plan),
        }

    def _build_plan_step(
        self,
        step: int,
        recommendation: dict[str, Any],
    ) -> dict[str, Any]:
        package_type = recommendation.get(
            "package_type",
            "manual_review_required",
        )

        if package_type == "file_integration_package":
            return {
                "step": step,
                "package_type": package_type,
                "generator": "File integration workflow / local runtime generator",
                "ready_to_execute": recommendation.get(
                    "ready_to_generate",
                    False,
                ),
                "reason": recommendation.get("reason", ""),
                "required_inputs": [
                    "customer_name",
                    "sample_input_file_path",
                    "confirmed_field_mapping",
                    "target_modula_format",
                    "input_folder",
                    "output_folder",
                ],
                "missing_inputs": recommendation.get("missing_inputs", []),
            }

        if package_type == "rest_integration_package":
            return {
                "step": step,
                "package_type": package_type,
                "generator": "RestIntegrationPackageGenerator",
                "ready_to_execute": recommendation.get(
                    "ready_to_generate",
                    False,
                ),
                "reason": recommendation.get("reason", ""),
                "required_inputs": [
                    "customer_name",
                    "pull_url",
                    "push_url",
                    "push_source_path",
                    "push_field_mapping",
                    "authentication_details",
                ],
                "missing_inputs": recommendation.get("missing_inputs", []),
            }

        if package_type == "sql_integration_package":
            return {
                "step": step,
                "package_type": package_type,
                "generator": "SQLIntegrationPackageGenerator",
                "ready_to_execute": recommendation.get(
                    "ready_to_generate",
                    False,
                ),
                "reason": recommendation.get("reason", ""),
                "required_inputs": [
                    "customer_name",
                    "connection_string",
                    "database_type",
                    "pull_query",
                    "push_source_path",
                    "push_target_table",
                    "push_field_mapping",
                ],
                "missing_inputs": recommendation.get("missing_inputs", []),
            }

        return {
            "step": step,
            "package_type": package_type,
            "generator": "Manual review required",
            "ready_to_execute": False,
            "reason": recommendation.get(
                "reason",
                "Package type is unclear.",
            ),
            "required_inputs": [
                "integration_method",
                "data_flow_details",
                "confirmed_mapping",
            ],
            "missing_inputs": recommendation.get(
                "missing_inputs",
                [
                    "Integration method",
                    "Data flow details",
                    "Confirmed mapping",
                ],
            ),
        }

    def _build_next_step(
        self,
        execution_plan: list[dict[str, Any]],
    ) -> str:
        if not execution_plan:
            return (
                "No execution plan was generated. Review the requirements and blueprint."
            )

        if all(step.get("ready_to_execute") for step in execution_plan):
            return (
                "All package generation steps are ready. Execute package generators."
            )

        return (
            "Collect missing inputs for each execution step before running package generators."
        )