"""
test_rest_package_generation.py

Tests end-to-end REST integration package generation.
"""

import json
import sys
from pathlib import Path

# Add the project root to the Python path so imports work when running
# this test directly from the tests/ directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.rest_api_integration_workflow import RestApiIntegrationWorkflow


def main():
    # Create a temporary source file for testing
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

    workflow = RestApiIntegrationWorkflow()

    result = workflow.generate_manual_package(
        customer_name="Ford Phase 2 Test",
        pull_url="https://jsonplaceholder.typicode.com/posts/1",
        push_url="https://jsonplaceholder.typicode.com/posts",
        push_source_path=str(source_path),
        push_field_mapping={
            "order_id": "id",
            "customer_name": "customer.name",
            "item": "lines[0].sku",
            "quantity": "lines[0].qty",
        },
    )

    print("=" * 70)
    print("REST PACKAGE GENERATION RESULT")
    print("=" * 70)
    print(json.dumps(result, indent=4))

    package_folder = Path(result["package"]["package_folder"])

    required_files = [
        "rest_pull_runner.py",
        "rest_push_runner.py",
        "rest_pull_config.json",
        "rest_push_config.json",
        "rest_pull_scheduler.py",
        "rest_push_scheduler.py",
    ]

    missing_files = []

    for filename in required_files:
        file_path = package_folder / filename

        if file_path.exists():
            print(f"✓ {filename}")
        else:
            print(f"✗ {filename}")
            missing_files.append(filename)

    if missing_files:
        raise RuntimeError(
            f"REST package generation failed. Missing files: {missing_files}"
        )

    print("\n✅ REST PACKAGE GENERATION TEST PASSED")


if __name__ == "__main__":
    main()