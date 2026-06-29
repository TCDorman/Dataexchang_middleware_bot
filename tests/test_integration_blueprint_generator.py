"""
test_integration_blueprint_generator.py

Tests AutoIntegrationWorkflow + IntegrationBlueprintGenerator.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.auto_integration_workflow import AutoIntegrationWorkflow
from agents.integration_blueprint_generator import IntegrationBlueprintGenerator


def main():
    requirements = """
Customer: Ford

ERP System:
SAP

Requirements:
- Orders are exported nightly as CSV files from SAP.
- Modula WMS must import those orders.
- Inventory transactions must be sent back to SAP through REST API.
- Serialized products require serial number tracking.
- Item master data should synchronize every 4 hours.
- Failed integrations must be logged and retried automatically.
"""

    auto_workflow = AutoIntegrationWorkflow()
    blueprint_generator = IntegrationBlueprintGenerator()

    auto_result = auto_workflow.run_from_requirements(
        requirements_text=requirements,
    )

    blueprint = blueprint_generator.generate_blueprint(
        analysis_result=auto_result,
        detected_integration_type=auto_result["detected_integration_type"],
        customer_name="Ford",
    )

    print("=" * 70)
    print("AUTO INTEGRATION RESULT")
    print("=" * 70)
    print(json.dumps(auto_result, indent=4))

    print("\n" + "=" * 70)
    print("INTEGRATION BLUEPRINT")
    print("=" * 70)
    print(json.dumps(blueprint, indent=4))

    if blueprint.get("status") != "success":
        raise RuntimeError("Blueprint generation failed.")

    if not blueprint.get("data_flows"):
        raise RuntimeError("Blueprint did not include data flows.")

    if not blueprint.get("required_packages"):
        raise RuntimeError("Blueprint did not include required packages.")

    print("\n✅ INTEGRATION BLUEPRINT TEST PASSED")


if __name__ == "__main__":
    main()