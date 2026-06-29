"""
test_integration_execution_orchestrator.py

Tests the full AI middleware assistant chain:
requirements -> planning -> generation plan -> execution orchestrator.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.auto_integration_workflow import AutoIntegrationWorkflow
from agents.integration_execution_orchestrator import (
    IntegrationExecutionOrchestrator,
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
    orchestrator = IntegrationExecutionOrchestrator()

    auto_result = auto_workflow.run_from_requirements(
        requirements_text=requirements,
    )

    execution_result = orchestrator.execute(
        auto_workflow_result=auto_result,
        discovered_inputs={},
    )

    print("=" * 70)
    print("INTEGRATION EXECUTION ORCHESTRATOR RESULT")
    print("=" * 70)
    print(json.dumps(execution_result, indent=4))

    if execution_result.get("status") != "success":
        raise RuntimeError("Integration execution orchestrator failed.")

    if "generation_result" not in execution_result:
        raise RuntimeError("Missing generation_result.")

    print("\n✅ INTEGRATION EXECUTION ORCHESTRATOR TEST PASSED")


if __name__ == "__main__":
    main()