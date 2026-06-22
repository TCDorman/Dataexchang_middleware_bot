"""
test_schema_inspector.py

Tests DBConnector and SchemaInspector using SQLite.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.connectors.db_connector import DBConnector
from src.connectors.schema_inspector import SchemaInspector


def main():
    db_path = PROJECT_ROOT / "data" / "test_sql" / "schema_test.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with DBConnector(str(db_path), database_type="sqlite") as db:
        db.execute("DROP TABLE IF EXISTS orders")
        db.execute(
            """
            CREATE TABLE orders (
                order_id TEXT PRIMARY KEY,
                customer_name TEXT NOT NULL,
                item TEXT NOT NULL,
                quantity INTEGER,
                created_at TEXT
            )
            """
        )

        db.execute(
            """
            INSERT INTO orders (
                order_id,
                customer_name,
                item,
                quantity,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            ["ORD-1001", "Ford", "ABC123", 5, "2026-06-22"],
        )

        inspector = SchemaInspector(db)

        result = inspector.inspect_database()

        print("=" * 70)
        print("SCHEMA INSPECTION RESULT")
        print("=" * 70)
        print(json.dumps(result, indent=4))

        tables = inspector.list_tables()

        if "orders" not in tables:
            raise RuntimeError("orders table was not discovered.")

        orders_schema = inspector.inspect_table("orders")

        column_names = [
            column["name"]
            for column in orders_schema["columns"]
        ]

        required_columns = [
            "order_id",
            "customer_name",
            "item",
            "quantity",
            "created_at",
        ]

        missing_columns = [
            column
            for column in required_columns
            if column not in column_names
        ]

        if missing_columns:
            raise RuntimeError(f"Missing expected columns: {missing_columns}")

        print("\n✅ SCHEMA INSPECTOR TEST PASSED")


if __name__ == "__main__":
    main()