"""
test_integration_execution_with_sql_inputs.py

Tests the full AI middleware assistant chain with real SQL generation inputs:

requirements -> planning -> execution orchestrator -> SQL package generated
"""

import csv
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
from src.connectors.db_connector import DBConnector


def main():
    test_sql_folder = PROJECT_ROOT / "data" / "test_sql"
    test_sql_folder.mkdir(parents=True, exist_ok=True)

    db_path = test_sql_folder / "auto_sql_test.db"
    source_path = test_sql_folder / "auto_sql_push_source.csv"
    output_folder = PROJECT_ROOT / "generated_integrations" / "ford_auto_sql"

    with DBConnector(str(db_path), database_type="sqlite") as db:
        db.execute("DROP TABLE IF EXISTS source_orders")
        db.execute("DROP TABLE IF EXISTS target_orders")

        db.execute(
            """
            CREATE TABLE source_orders (
                order_id TEXT PRIMARY KEY,
                customer_name TEXT,
                item TEXT,
                quantity INTEGER
            )
            """
        )

        db.execute(
            """
            CREATE TABLE target_orders (
                order_id TEXT PRIMARY KEY,
                customer_name TEXT,
                item TEXT,
                quantity INTEGER
            )
            """
        )

        db.execute(
            """
            INSERT INTO source_orders (
                order_id,
                customer_name,
                item,
                quantity
            )
            VALUES (?, ?, ?, ?)
            """,
            ["ORD-1001", "Ford", "ABC123", 5],
        )

    with open(source_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "order_id",
                "customer_name",
                "item",
                "quantity",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "order_id": "ORD-2001",
                "customer_name": "Ford",
                "item": "XYZ789",
                "quantity": "2",
            }
        )

    requirements = """
Customer: Ford

ERP System:
SAP

Requirements:
- Orders are available in a shared SQL database table.
- Modula WMS must pull orders from the SQL source table.
- Inventory updates must be written back into a SQL target table.
- Failed integrations must be logged and retried automatically.
"""

    auto_workflow = AutoIntegrationWorkflow()
    orchestrator = IntegrationExecutionOrchestrator()

    auto_result = auto_workflow.run_from_requirements(
        requirements_text=requirements,
    )

    discovered_inputs = {
        "sql_integration_package": {
            "customer_name": "Ford Auto SQL",
            "output_folder": str(output_folder),
            "connection_string": str(db_path),
            "database_type": "sqlite",
            "pull_query": (
                "SELECT order_id, customer_name, item, quantity "
                "FROM source_orders"
            ),
            "push_source_path": str(source_path),
            "push_target_table": "target_orders",
            "push_field_mapping": {
                "order_id": "order_id",
                "customer_name": "customer_name",
                "item": "item",
                "quantity": "quantity",
            },
        }
    }

    execution_result = orchestrator.execute(
        auto_workflow_result=auto_result,
        discovered_inputs=discovered_inputs,
    )

    print("=" * 70)
    print("SQL AUTO EXECUTION RESULT")
    print("=" * 70)
    print(json.dumps(execution_result, indent=4))

    generation_result = execution_result.get("generation_result", {})
    generated_packages = generation_result.get("generated_packages", [])

    if execution_result.get("status") != "success":
        raise RuntimeError("Execution orchestrator failed.")

    if not generated_packages:
        raise RuntimeError("No SQL package was generated.")

    required_files = [
        "sql_pull_runner.py",
        "sql_push_runner.py",
        "sql_pull_config.json",
        "sql_push_config.json",
    ]

    missing_files = [
        filename
        for filename in required_files
        if not (output_folder / filename).exists()
    ]

    if missing_files:
        raise RuntimeError(f"Missing generated SQL files: {missing_files}")

    print("\n✅ SQL AUTO EXECUTION TEST PASSED")


if __name__ == "__main__":
    main()