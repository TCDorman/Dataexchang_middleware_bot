"""
auto_package_generation_workflow.py

Processes a package generation plan and automatically runs package generators
when enough generation inputs are available.

Version 2 supports:
1. REST package generation
2. SQL package generation
3. Missing-input detection
4. Safe skipping when required inputs are unavailable
"""

from typing import Any

from src.generators.rest_integration_package_generator import (
    RestIntegrationPackageGenerator,
)
from src.generators.sql_integration_package_generator import (
    SQLIntegrationPackageGenerator,
)


class AutoPackageGenerationWorkflow:
    """
    Evaluates generation plan steps and runs available package generators.
    """

    def __init__(self):
        self.rest_generator = RestIntegrationPackageGenerator()
        self.sql_generator = SQLIntegrationPackageGenerator()

    def run_generation_plan(
        self,
        generation_plan: dict[str, Any],
        generation_inputs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        execution_plan = generation_plan.get("execution_plan", [])
        generation_inputs = generation_inputs or {}

        generated_packages = []
        skipped_packages = []
        failed_packages = []

        for step in execution_plan:
            result = self._process_step(
                step=step,
                generation_inputs=generation_inputs,
            )

            if result["status"] == "generated":
                generated_packages.append(result)

            elif result["status"] in [
                "skipped_missing_inputs",
                "manual_review_required",
                "unsupported_package_type",
            ]:
                skipped_packages.append(result)

            else:
                failed_packages.append(result)

        return {
            "status": "success",
            "workflow": "auto_package_generation",
            "customer_name": generation_plan.get(
                "customer_name",
                "unknown_customer",
            ),
            "integration_type": generation_plan.get(
                "integration_type",
                "unclear",
            ),
            "generated_packages": generated_packages,
            "skipped_packages": skipped_packages,
            "failed_packages": failed_packages,
            "summary": {
                "generated_count": len(generated_packages),
                "skipped_count": len(skipped_packages),
                "failed_count": len(failed_packages),
            },
            "next_step": self._build_next_step(
                generated_packages=generated_packages,
                skipped_packages=skipped_packages,
                failed_packages=failed_packages,
            ),
        }

    def _process_step(
        self,
        step: dict[str, Any],
        generation_inputs: dict[str, Any],
    ) -> dict[str, Any]:
        package_type = step.get("package_type", "manual_review_required")

        if package_type == "manual_review_required":
            return {
                "status": "manual_review_required",
                "step": step.get("step"),
                "package_type": package_type,
                "generator": step.get("generator"),
                "reason": step.get(
                    "reason",
                    "Package type requires manual review.",
                ),
                "missing_inputs": step.get("missing_inputs", []),
            }

        package_inputs = generation_inputs.get(package_type, {})

        if package_type == "rest_integration_package":
            return self._generate_rest_package(
                step=step,
                package_inputs=package_inputs,
            )

        if package_type == "sql_integration_package":
            return self._generate_sql_package(
                step=step,
                package_inputs=package_inputs,
            )

        if package_type == "file_integration_package":
            return {
                "status": "unsupported_package_type",
                "step": step.get("step"),
                "package_type": package_type,
                "generator": step.get("generator"),
                "reason": (
                    "Automatic file package generation is not connected yet. "
                    "Use the existing file workflow/local runtime generator manually."
                ),
                "missing_inputs": step.get("missing_inputs", []),
                "required_inputs": step.get("required_inputs", []),
            }

        return {
            "status": "unsupported_package_type",
            "step": step.get("step"),
            "package_type": package_type,
            "generator": step.get("generator"),
            "reason": "Unsupported package type.",
            "missing_inputs": step.get("missing_inputs", []),
            "required_inputs": step.get("required_inputs", []),
        }

    def _generate_rest_package(
        self,
        step: dict[str, Any],
        package_inputs: dict[str, Any],
    ) -> dict[str, Any]:
        required_fields = [
            "customer_name",
            "output_folder",
            "pull_url",
            "push_url",
            "push_source_path",
            "push_field_mapping",
        ]

        missing_inputs = self._get_missing_required_fields(
            package_inputs=package_inputs,
            required_fields=required_fields,
        )

        if missing_inputs:
            return {
                "status": "skipped_missing_inputs",
                "step": step.get("step"),
                "package_type": "rest_integration_package",
                "generator": "RestIntegrationPackageGenerator",
                "reason": "REST package inputs are incomplete.",
                "missing_inputs": missing_inputs,
                "required_inputs": required_fields,
            }

        try:
            package_result = self.rest_generator.generate_package(
                customer_name=package_inputs["customer_name"],
                output_folder=package_inputs["output_folder"],
                pull_url=package_inputs["pull_url"],
                push_url=package_inputs["push_url"],
                push_source_path=package_inputs["push_source_path"],
                push_field_mapping=package_inputs["push_field_mapping"],
            )

            return {
                "status": "generated",
                "step": step.get("step"),
                "package_type": "rest_integration_package",
                "generator": "RestIntegrationPackageGenerator",
                "package_result": package_result,
            }

        except Exception as error:
            return {
                "status": "failed",
                "step": step.get("step"),
                "package_type": "rest_integration_package",
                "generator": "RestIntegrationPackageGenerator",
                "error": str(error),
            }

    def _generate_sql_package(
        self,
        step: dict[str, Any],
        package_inputs: dict[str, Any],
    ) -> dict[str, Any]:
        required_fields = [
            "customer_name",
            "output_folder",
            "connection_string",
            "pull_query",
            "push_source_path",
            "push_target_table",
            "push_field_mapping",
        ]

        missing_inputs = self._get_missing_required_fields(
            package_inputs=package_inputs,
            required_fields=required_fields,
        )

        if missing_inputs:
            return {
                "status": "skipped_missing_inputs",
                "step": step.get("step"),
                "package_type": "sql_integration_package",
                "generator": "SQLIntegrationPackageGenerator",
                "reason": "SQL package inputs are incomplete.",
                "missing_inputs": missing_inputs,
                "required_inputs": required_fields,
            }

        try:
            package_result = self.sql_generator.generate_package(
                customer_name=package_inputs["customer_name"],
                output_folder=package_inputs["output_folder"],
                connection_string=package_inputs["connection_string"],
                pull_query=package_inputs["pull_query"],
                push_source_path=package_inputs["push_source_path"],
                push_target_table=package_inputs["push_target_table"],
                push_field_mapping=package_inputs["push_field_mapping"],
                database_type=package_inputs.get("database_type", "sqlite"),
            )

            return {
                "status": "generated",
                "step": step.get("step"),
                "package_type": "sql_integration_package",
                "generator": "SQLIntegrationPackageGenerator",
                "package_result": package_result,
            }

        except Exception as error:
            return {
                "status": "failed",
                "step": step.get("step"),
                "package_type": "sql_integration_package",
                "generator": "SQLIntegrationPackageGenerator",
                "error": str(error),
            }

    def _get_missing_required_fields(
        self,
        package_inputs: dict[str, Any],
        required_fields: list[str],
    ) -> list[str]:
        missing = []

        for field in required_fields:
            value = package_inputs.get(field)

            if value is None:
                missing.append(field)

            elif isinstance(value, str) and not value.strip():
                missing.append(field)

            elif isinstance(value, dict) and not value:
                missing.append(field)

            elif isinstance(value, list) and not value:
                missing.append(field)

        return missing

    def _build_next_step(
        self,
        generated_packages: list[dict[str, Any]],
        skipped_packages: list[dict[str, Any]],
        failed_packages: list[dict[str, Any]],
    ) -> str:
        if failed_packages:
            return (
                "Review failed package generation steps and fix the reported errors."
            )

        if skipped_packages and generated_packages:
            return (
                "Some packages were generated and others were skipped. "
                "Collect missing inputs for skipped packages and rerun generation."
            )

        if skipped_packages:
            return (
                "No packages were generated. Collect the missing inputs for skipped packages and rerun generation."
            )

        if generated_packages:
            return (
                "All eligible packages were generated successfully."
            )

        return (
            "No package generation steps were available. Review the generation plan."
        )