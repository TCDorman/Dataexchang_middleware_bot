"""
test_integration_execution_with_rest_inputs.py

Tests the full AI middleware assistant chain with real REST generation inputs:

requirements -> planning -> execution orchestrator -> REST package generated
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
    test_data_folder = PROJECT_ROOT / "data" / "test_rest_push"
    test_data_folder.mkdir(parents=True, exist_ok=True)

    source_path = test_data_folder / "orders.csv"

    source_path.write_text(
        (
            "order_id,customer_name,item,quantity\n"
            "ORD-1001,Ford,ABC123,5\n"
            "ORD-1002,Ford,XYZ789,2\n"
        ),
        encoding="utf-8",
    )

    output_folder = PROJECT_ROOT / "generated_integrations" / "ford_auto_rest"

    requirements = """
Customer: Ford

ERP System:
SAP

Requirements:
- Orders are exchanged through REST API.
- Modula WMS must pull order data from the ERP API.
- Modula WMS must push inventory transaction updates back to SAP through REST API.
- Failed integrations must be logged and retried automatically.
"""

    auto_workflow = AutoIntegrationWorkflow()
    orchestrator = IntegrationExecutionOrchestrator()

    auto_result = auto_workflow.run_from_requirements(
        requirements_text=requirements,
    )

    discovered_inputs = {
        "rest_integration_package": {
            "customer_name": "Ford Auto REST",
            "output_folder": str(output_folder),
            "pull_url": "https://jsonplaceholder.typicode.com/posts/1",
            "push_url": "https://jsonplaceholder.typicode.com/posts",
            "push_source_path": str(source_path),
            "push_field_mapping": {
                "order_id": "id",
                "customer_name": "customer.name",
                "item": "lines[0].sku",
                "quantity": "lines[0].qty",
            },
        }
    }

    execution_result = orchestrator.execute(
        auto_workflow_result=auto_result,
        discovered_inputs=discovered_inputs,
    )

    print("=" * 70)
    print("REST AUTO EXECUTION RESULT")
    print("=" * 70)
    print(json.dumps(execution_result, indent=4))

    generation_result = execution_result.get("generation_result", {})
    generated_packages = generation_result.get("generated_packages", [])

    if execution_result.get("status") != "success":
        raise RuntimeError("Execution orchestrator failed.")

    if not generated_packages:
        raise RuntimeError("No REST package was generated.")

    required_files = [
        "rest_pull_runner.py",
        "rest_push_runner.py",
        "rest_pull_config.json",
        "rest_push_config.json",
        "rest_pull_scheduler.py",
        "rest_push_scheduler.py",
    ]

    missing_files = [
        filename
        for filename in required_files
        if not (output_folder / filename).exists()
    ]

    if missing_files:
        raise RuntimeError(f"Missing generated REST files: {missing_files}")

    print("\n✅ REST AUTO EXECUTION TEST PASSED")


if __name__ == "__main__":
    main()