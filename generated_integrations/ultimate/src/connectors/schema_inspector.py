"""
schema_inspector.py

Inspects database tables and columns for SQL integrations.
"""

from typing import Any

from src.connectors.db_connector import DBConnector


class SchemaInspector:
    """
    Reads database schema information and sample values.
    """

    def __init__(
        self,
        connector: DBConnector,
    ):
        self.connector = connector

    def list_tables(self) -> list[str]:
        if self.connector.database_type == "sqlite":
            rows = self.connector.fetch_all(
                """
                SELECT name
                FROM sqlite_master
                WHERE type IN ('table', 'view')
                AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            )

            return [row["name"] for row in rows]

        rows = self.connector.fetch_all(
            """
            SELECT TABLE_NAME AS table_name
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE IN ('BASE TABLE', 'VIEW')
            ORDER BY TABLE_NAME
            """
        )

        return [row["table_name"] for row in rows]

    def get_columns(
        self,
        table_name: str,
    ) -> list[dict[str, Any]]:
        if self.connector.database_type == "sqlite":
            rows = self.connector.fetch_all(f"PRAGMA table_info({table_name})")

            return [
                {
                    "name": row["name"],
                    "type": self._normalize_sql_type(row["type"]),
                    "raw_type": row["type"],
                    "nullable": not bool(row["notnull"]),
                    "primary_key": bool(row["pk"]),
                }
                for row in rows
            ]

        rows = self.connector.fetch_all(
            """
            SELECT
                COLUMN_NAME AS name,
                DATA_TYPE AS raw_type,
                IS_NULLABLE AS is_nullable
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
            """,
            [table_name],
        )

        return [
            {
                "name": row["name"],
                "type": self._normalize_sql_type(row["raw_type"]),
                "raw_type": row["raw_type"],
                "nullable": str(row["is_nullable"]).upper() == "YES",
                "primary_key": False,
            }
            for row in rows
        ]

    def inspect_table(
        self,
        table_name: str,
        sample_limit: int = 5,
    ) -> dict[str, Any]:
        columns = self.get_columns(table_name)
        sample_rows = self.get_sample_rows(table_name, sample_limit)

        return {
            "table_name": table_name,
            "columns": columns,
            "sample_rows": sample_rows,
            "sample_count": len(sample_rows),
        }

    def get_sample_rows(
        self,
        table_name: str,
        sample_limit: int = 5,
    ) -> list[dict[str, Any]]:
        if self.connector.database_type == "sqlite":
            return self.connector.fetch_all(
                f"SELECT * FROM {table_name} LIMIT ?",
                [sample_limit],
            )

        return self.connector.fetch_all(
            f"SELECT TOP {sample_limit} * FROM {table_name}"
        )

    def inspect_database(self) -> dict[str, Any]:
        tables = self.list_tables()

        return {
            "database_type": self.connector.database_type,
            "tables": [
                self.inspect_table(table_name)
                for table_name in tables
            ],
        }

    def _normalize_sql_type(
        self,
        raw_type: str | None,
    ) -> str:
        if not raw_type:
            return "string"

        raw = raw_type.lower()

        if any(token in raw for token in ["char", "text", "varchar", "nvarchar"]):
            return "string"

        if any(token in raw for token in ["int", "bigint", "smallint", "tinyint"]):
            return "integer"

        if any(token in raw for token in ["decimal", "numeric", "float", "real", "money"]):
            return "float"

        if any(token in raw for token in ["bit", "bool"]):
            return "boolean"

        if any(token in raw for token in ["date", "time"]):
            return "datetime"

        return "string"