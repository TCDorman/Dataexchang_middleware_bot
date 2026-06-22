"""
test_sql_phase3_foundation.py

Tests the Phase 3 SQL foundation workflow.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.connectors.db_connector import DBConnector
from src.connectors.schema_inspector import SchemaInspector
from src.connectors.sql_discovery import SQLDiscovery
from src.connectors.sql_normalizer import SQLNormalizer
from src.connectors.sql_query_builder import SQLQueryBuilder


def main():
    db_path = PROJECT_ROOT / "data" / "test_sql" / "phase3_foundation.db"
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
        discovery = SQLDiscovery(inspector)
        normalizer = SQLNormalizer()
        query_builder = SQLQueryBuilder()

        tables = discovery.list_sources()
        if "orders" not in tables:
            raise RuntimeError("orders table was not discovered.")

        table_schema = discovery.get_source_summary("orders")
        normalized_schema = normalizer.normalize_table_schema(table_schema)

        source_config = discovery.build_source_config(
            connection_string=str(db_path),
            source_table="orders",
            selected_columns=[],
            direction="pull",
        )

        query_result = query_builder.build_select_query(
            source_config=source_config,
            field_mapping={
                "order_id": "order_id",
                "customer_name": "customer_name",
                "item": "item",
                "quantity": "quantity",
            },
        )

        rows = db.fetch_all(query_result["sql"], query_result["params"])

        result = {
            "tables": tables,
            "normalized_schema": normalized_schema,
            "query": query_result,
            "rows": rows,
        }

        print("=" * 70)
        print("PHASE 3 SQL FOUNDATION TEST")
        print("=" * 70)
        print(json.dumps(result, indent=4))

        if not rows:
            raise RuntimeError("Generated SQL query returned no rows.")

        print("\n✅ PHASE 3 SQL FOUNDATION TEST PASSED")


if __name__ == "__main__":
    main()