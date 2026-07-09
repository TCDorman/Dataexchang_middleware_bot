"""
sql_query_executor.py

Executes SQL queries and returns rows as dictionaries.

This module will be used by SQL-to-Modula workflows
to pull live order data from ERP databases.
"""

from typing import Any


class SqlQueryExecutor:

    def execute_query(
        self,
        connection_string: str,
        query: str,
    ) -> list[dict[str, Any]]:

        try:
            import pyodbc
        except ImportError:
            raise ImportError(
                "pyodbc is not installed. Run: pip install pyodbc"
            )

        connection = pyodbc.connect(
            connection_string,
            timeout=10,
        )

        cursor = connection.cursor()

        cursor.execute(query)

        columns = [column[0] for column in cursor.description]

        rows = []

        for record in cursor.fetchall():
            row = {}

            for index, value in enumerate(record):
                row[columns[index]] = value

            rows.append(row)

        cursor.close()
        connection.close()

        return rows