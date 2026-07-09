"""
integration_blueprint_generator.py

Converts AI requirements analysis output into a structured integration
blueprint that can later drive package generation.

The blueprint is the bridge between:
1. Customer requirements
2. AI analysis
3. Middleware package generation
"""

from typing import Any


class IntegrationBlueprintGenerator:
    """
    Builds implementation-ready integration blueprints from
    RequirementsAnalysisAgent / AutoIntegrationWorkflow output.
    """

    def generate_blueprint(
        self,
        analysis_result: dict[str, Any],
        detected_integration_type: str,
        customer_name: str | None = None,
    ) -> dict[str, Any]:
        analysis = analysis_result.get("analysis", analysis_result)

        resolved_customer_name = (
            customer_name
            or self._infer_customer_name(analysis)
            or "unknown_customer"
        )

        data_flows = self._build_data_flows(
            analysis.get("data_flows", [])
        )

        required_packages = self._determine_required_packages(
            detected_integration_type=detected_integration_type,
            data_flows=data_flows,
        )

        return {
            "status": "success",
            "customer_name": resolved_customer_name,
            "integration_type": detected_integration_type,
            "source_systems": analysis.get("source_systems", []),
            "target_systems": analysis.get("target_systems", ["Modula WMS"]),
            "data_flows": data_flows,
            "required_packages": required_packages,
            "field_mapping_candidates": analysis.get(
                "field_mapping_candidates",
                [],
            ),
            "transformation_rules": analysis.get(
                "transformation_rules",
                [],
            ),
            "error_handling_recommendations": analysis.get(
                "error_handling_recommendations",
                [],
            ),
            "customer_clarification_questions": analysis.get(
                "customer_clarification_questions",
                [],
            ),
            "risk_flags": analysis.get("risk_flags", []),
            "recommended_mapping_profile": self._build_mapping_profile_name(
                resolved_customer_name,
            ),
            "implementation_complexity": self._estimate_complexity(
                detected_integration_type=detected_integration_type,
                data_flows=data_flows,
                risk_flags=analysis.get("risk_flags", []),
            ),
            "package_generation_ready": False,
            "next_step": (
                "Review blueprint, confirm missing technical details, "
                "then generate the required package components."
            ),
        }

    def _build_data_flows(
        self,
        raw_flows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        flows = []

        for index, flow in enumerate(raw_flows, start=1):
            data_object = (
                flow.get("data_object")
                or flow.get("flow_name")
                or f"flow_{index}"
            )

            flows.append(
                {
                    "name": flow.get("flow_name") or str(data_object),
                    "direction": flow.get("direction", "unknown"),
                    "source_system": flow.get("source_system", ""),
                    "target_system": flow.get("target_system", ""),
                    "data_object": data_object,
                    "method": flow.get(
                        "recommended_exchange_method",
                        "unknown",
                    ),
                    "frequency": flow.get("frequency", ""),
                    "notes": flow.get("notes", ""),
                }
            )

        return flows

    def _determine_required_packages(
        self,
        detected_integration_type: str,
        data_flows: list[dict[str, Any]],
    ) -> list[str]:
        packages = set()

        if detected_integration_type == "file":
            packages.add("file_integration_package")

        elif detected_integration_type == "rest_api":
            packages.add("rest_integration_package")

        elif detected_integration_type == "sql":
            packages.add("sql_integration_package")

        elif detected_integration_type == "hybrid":
            for flow in data_flows:
                method = str(flow.get("method", "")).lower()

                if any(
                    token in method
                    for token in ["csv", "file", "json", "xml", "excel"]
                ):
                    packages.add("file_integration_package")

                if any(
                    token in method
                    for token in ["rest", "api", "http", "web service"]
                ):
                    packages.add("rest_integration_package")

                if any(
                    token in method
                    for token in ["sql", "odbc", "database", "table"]
                ):
                    packages.add("sql_integration_package")

        if not packages:
            packages.add("manual_review_required")

        return sorted(packages)

    def _estimate_complexity(
        self,
        detected_integration_type: str,
        data_flows: list[dict[str, Any]],
        risk_flags: list[Any],
    ) -> str:
        score = 0

        if detected_integration_type == "hybrid":
            score += 2

        if len(data_flows) >= 3:
            score += 2
        elif len(data_flows) == 2:
            score += 1

        if risk_flags:
            score += 1

        if score >= 4:
            return "high"

        if score >= 2:
            return "medium"

        return "low"

    def _infer_customer_name(
        self,
        analysis: dict[str, Any],
    ) -> str | None:
        summary = str(analysis.get("integration_summary", ""))

        known_markers = [
            "Customer:",
            "customer:",
            "Client:",
            "client:",
        ]

        for marker in known_markers:
            if marker in summary:
                after_marker = summary.split(marker, 1)[1].strip()
                return after_marker.split()[0].strip(".,:")

        return None

    def _build_mapping_profile_name(
        self,
        customer_name: str,
    ) -> str:
        safe_name = customer_name.strip().lower().replace(" ", "_")
        return f"{safe_name}_profile.json"