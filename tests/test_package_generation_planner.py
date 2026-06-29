"""
test_package_generation_planner.py

Tests the full AI planning chain:
requirements -> auto workflow -> package recommendation -> generation plan.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.auto_integration_workflow import AutoIntegrationWorkflow
from agents.package_generation_planner import PackageGenerationPlanner


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
    planner = PackageGenerationPlanner()

    auto_result = auto_workflow.run_from_requirements(
        requirements_text=requirements,
    )

    plan = planner.build_plan(
        package_recommendation=auto_result["package_recommendation"],
    )

    print("=" * 70)
    print("AUTO WORKFLOW RESULT")
    print("=" * 70)
    print(json.dumps(auto_result, indent=4))

    print("\n" + "=" * 70)
    print("PACKAGE GENERATION PLAN")
    print("=" * 70)
    print(json.dumps(plan, indent=4))

    if plan.get("status") != "success":
        raise RuntimeError("Package generation plan failed.")

    if not plan.get("execution_plan"):
        raise RuntimeError("No execution plan was generated.")

    print("\n✅ PACKAGE GENERATION PLANNER TEST PASSED")


if __name__ == "__main__":
    main()