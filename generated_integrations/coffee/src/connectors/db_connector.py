"""
db_connector.py

Reusable database connector for SQL / ODBC integrations.

Supports:
1. SQLite for local testing
2. ODBC connection strings for SQL Server and other databases
3. Parameterized query execution
4. Context manager usage
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class DBConnector:
    """
    Database connector used by SQL integration workflows.

    SQLite is supported directly for testing.
    ODBC connections are supported through pyodbc when installed.
    """

    def __init__(
        self,
        connection_string: str,
        database_type: str = "sqlite",
    ):
        self.connection_string = connection_string
        self.database_type = database_type.lower()
        self.connection = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        self.close()

    def connect(self):
        """
        Open a database connection.
        """

        if self.database_type == "sqlite":
            db_path = Path(self.connection_string)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(str(db_path))
            self.connection.row_factory = sqlite3.Row
            return self.connection

        if self.database_type in ("sql_server", "odbc"):
            try:
                import pyodbc
            except ImportError as error:
                raise ImportError(
                    "pyodbc is required for SQL Server / ODBC connections. "
                    "Install it with: pip install pyodbc"
                ) from error

            self.connection = pyodbc.connect(self.connection_string)
            return self.connection

        raise ValueError(f"Unsupported database_type: {self.database_type}")

    def close(self) -> None:
        """
        Close the active connection.
        """

        if self.connection:
            self.connection.close()
            self.connection = None

    def execute(
        self,
        sql: str,
        params: tuple[Any, ...] | list[Any] | None = None,
    ) -> int:
        """
        Execute INSERT, UPDATE, DELETE, or DDL SQL.

        Always pass values through params instead of string formatting.
        """

        connection = self._get_connection()
        cursor = connection.cursor()

        cursor.execute(sql, params or [])
        connection.commit()

        return cursor.rowcount

    def fetch_all(
        self,
        sql: str,
        params: tuple[Any, ...] | list[Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Execute a SELECT query and return all rows as dictionaries.
        """

        connection = self._get_connection()
        cursor = connection.cursor()

        cursor.execute(sql, params or [])
        rows = cursor.fetchall()

        return [self._row_to_dict(row, cursor) for row in rows]

    def fetch_one(
        self,
        sql: str,
        params: tuple[Any, ...] | list[Any] | None = None,
    ) -> dict[str, Any] | None:
        """
        Execute a SELECT query and return one row as a dictionary.
        """

        connection = self._get_connection()
        cursor = connection.cursor()

        cursor.execute(sql, params or [])
        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_dict(row, cursor)

    def test_connection(self) -> dict[str, Any]:
        """
        Verify that the database connection works.
        """

        try:
            self.connect()

            if self.database_type == "sqlite":
                result = self.fetch_one("SELECT 1 AS connection_test")
            else:
                result = self.fetch_one("SELECT 1 AS connection_test")

            return {
                "status": "success",
                "database_type": self.database_type,
                "result": result,
            }

        except Exception as error:
            return {
                "status": "error",
                "database_type": self.database_type,
                "error": str(error),
            }

        finally:
            self.close()

    def _get_connection(self):
        if self.connection is None:
            self.connect()

        return self.connection

    def _row_to_dict(
        self,
        row,
        cursor,
    ) -> dict[str, Any]:
        if isinstance(row, sqlite3.Row):
            return dict(row)

        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, row))