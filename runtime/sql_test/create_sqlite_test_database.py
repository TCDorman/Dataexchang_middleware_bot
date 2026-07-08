"""
create_sqlite_test_database.py

Creates a sample SQLite ERP database for testing
SQL/ODBC import functionality.
"""

import sqlite3
from pathlib import Path


DB_PATH = Path("runtime/sql/customer_orders.db")


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("DROP TABLE IF EXISTS orders_to_modula")

    cursor.execute(
        """
        CREATE TABLE orders_to_modula (
            order_id TEXT NOT NULL,
            customer_name TEXT,
            item TEXT NOT NULL,
            quantity REAL NOT NULL
        )
        """
    )

    rows = [
        ("PO10001", "BOTW Industries", "BRG-100", 10),
        ("PO10001", "BOTW Industries", "CBL-100", 5),
        ("PO10002", "BOTW Industries", "CBL-200", 8),
    ]

    cursor.executemany(
        """
        INSERT INTO orders_to_modula (
            order_id,
            customer_name,
            item,
            quantity
        )
        VALUES (?, ?, ?, ?)
        """,
        rows,
    )

    connection.commit()
    connection.close()

    print("=" * 60)
    print("SQLite test database created successfully.")
    print(f"Database: {DB_PATH}")
    print("Table: orders_to_modula")
    print(f"Rows inserted: {len(rows)}")
    print("=" * 60)


if __name__ == "__main__":
    main()