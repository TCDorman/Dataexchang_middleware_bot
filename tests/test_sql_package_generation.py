"""
test_sql_package_generation.py

Tests SQL integration package generation and generated runners.
"""

import csv
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.connectors.db_connector import DBConnector
from src.generators.sql_integration_package_generator import (
    SQLIntegrationPackageGenerator,
)


def main():
    db_path = PROJECT_ROOT / "data" / "test_sql" / "sql_package_test.db"
    source_path = PROJECT_ROOT / "data" / "test_sql" / "sql_push_source.csv"
    package_folder = PROJECT_ROOT / "generated_integrations" / "sql_phase_3_test"

    db_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.parent.mkdir(parents=True, exist_ok=True)

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

    generator = SQLIntegrationPackageGenerator()

    result = generator.generate_package(
        customer_name="SQL Phase 3 Test",
        output_folder=str(package_folder),
        connection_string=str(db_path),
        database_type="sqlite",
        pull_query="SELECT order_id, customer_name, item, quantity FROM source_orders",
        push_source_path=str(source_path),
        push_target_table="target_orders",
        push_field_mapping={
            "order_id": "order_id",
            "customer_name": "customer_name",
            "item": "item",
            "quantity": "quantity",
        },
    )

    print("=" * 70)
    print("SQL PACKAGE GENERATION RESULT")
    print("=" * 70)
    print(json.dumps(result, indent=4))

    required_files = [
        "sql_pull_runner.py",
        "sql_push_runner.py",
        "sql_pull_config.json",
        "sql_push_config.json",
    ]

    missing_files = [
        filename
        for filename in required_files
        if not (package_folder / filename).exists()
    ]

    if missing_files:
        raise RuntimeError(f"Missing generated files: {missing_files}")

    pull_result = subprocess.run(
        [
            sys.executable,
            str(package_folder / "sql_pull_runner.py"),
            "--config",
            str(package_folder / "sql_pull_config.json"),
            "--once",
            "--dry-run",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    print("\nSQL PULL DRY-RUN STDOUT:")
    print(pull_result.stdout)

    if pull_result.returncode != 0:
        print(pull_result.stderr)
        raise RuntimeError("SQL pull dry-run failed.")

    push_result = subprocess.run(
        [
            sys.executable,
            str(package_folder / "sql_push_runner.py"),
            "--config",
            str(package_folder / "sql_push_config.json"),
            "--once",
            "--dry-run",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    print("\nSQL PUSH DRY-RUN STDOUT:")
    print(push_result.stdout)

    if push_result.returncode != 0:
        print(push_result.stderr)
        raise RuntimeError("SQL push dry-run failed.")

    print("\n✅ SQL PACKAGE GENERATION TEST PASSED")


if __name__ == "__main__":
    main()