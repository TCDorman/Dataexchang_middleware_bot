"""
test_auto_package_generation_workflow.py

Tests the complete AI middleware planning chain through the
AutoPackageGenerationWorkflow.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.auto_integration_workflow import AutoIntegrationWorkflow
from agents.auto_package_generation_workflow import (
    AutoPackageGenerationWorkflow,
)


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

    auto_result = auto_workflow.run_from_requirements(
        requirements_text=requirements,
    )

    package_generation_workflow = AutoPackageGenerationWorkflow()

    generation_result = package_generation_workflow.run_generation_plan(
        generation_plan=auto_result["generation_plan"],
    )

    print("=" * 70)
    print("AUTO PACKAGE GENERATION WORKFLOW RESULT")
    print("=" * 70)
    print(json.dumps(generation_result, indent=4))

    if generation_result.get("status") != "success":
        raise RuntimeError("Auto package generation workflow failed.")

    if "summary" not in generation_result:
        raise RuntimeError("Generation result is missing summary.")

    print("\n✅ AUTO PACKAGE GENERATION WORKFLOW TEST PASSED")


if __name__ == "__main__":
    main()