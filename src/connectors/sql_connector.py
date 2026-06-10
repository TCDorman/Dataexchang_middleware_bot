"""
sql_connector.py

SQL / ODBC connector for direct database integrations.

This connector:
1. Accepts an ODBC connection string
2. Connects to the database using pyodbc
3. Discovers available tables
4. Reads table column schemas
5. Flags likely order header and order line tables
"""

from __future__ import annotations

from typing import Any


class SqlConnector:
    """
    SQL connector used for schema discovery.
    """

    def analyze_connection_string(self, connection_string: str) -> dict:
        try:
            import pyodbc
        except ImportError:
            return {
                "status": "error",
                "source_type": "sql",
                "message": "pyodbc is not installed. Run: pip install pyodbc",
                "connection_preview": self._mask_connection_string(connection_string),
            }

        try:
            connection = pyodbc.connect(connection_string, timeout=5)
            cursor = connection.cursor()

            tables = self._discover_tables(cursor)
            schema = self._discover_schema(cursor, tables)

            cursor.close()
            connection.close()

            return {
                "status": "success",
                "source_type": "sql",
                "message": "SQL / ODBC schema discovery completed successfully.",
                "connection_preview": self._mask_connection_string(connection_string),
                "tables_found": len(tables),
                "tables": schema,
                "suggestions": self._suggest_order_tables(schema),
            }

        except Exception as error:
            return {
                "status": "error",
                "source_type": "sql",
                "message": "SQL / ODBC schema discovery failed.",
                "error": str(error),
                "connection_preview": self._mask_connection_string(connection_string),
            }

    def _discover_tables(self, cursor: Any) -> list[dict]:
        tables = []

        for row in cursor.tables(tableType="TABLE"):
            table = {
                "table_catalog": getattr(row, "table_cat", None),
                "table_schema": getattr(row, "table_schem", None),
                "table_name": getattr(row, "table_name", None),
                "table_type": getattr(row, "table_type", None),
            }

            if table["table_name"]:
                tables.append(table)

        return tables

    def _discover_schema(self, cursor: Any, tables: list[dict]) -> list[dict]:
        schema = []

        for table in tables:
            table_schema = table.get("table_schema")
            table_name = table.get("table_name")

            columns = []

            try:
                for column in cursor.columns(
                    table=table_name,
                    schema=table_schema,
                ):
                    columns.append(
                        {
                            "column_name": getattr(column, "column_name", None),
                            "data_type": getattr(column, "type_name", None),
                            "nullable": getattr(column, "nullable", None),
                            "column_size": getattr(column, "column_size", None),
                        }
                    )

            except Exception as error:
                columns.append(
                    {
                        "error": f"Could not read columns for table {table_name}: {error}"
                    }
                )

            schema.append(
                {
                    "table_schema": table_schema,
                    "table_name": table_name,
                    "columns": columns,
                }
            )

        return schema

    def _suggest_order_tables(self, schema: list[dict]) -> dict:
        header_candidates = []
        line_candidates = []

        header_keywords = [
            "order",
            "orders",
            "salesorder",
            "sales_order",
            "shipment",
            "pick",
        ]

        line_keywords = [
            "line",
            "lines",
            "detail",
            "details",
            "item",
            "items",
            "orderline",
            "order_line",
        ]

        for table in schema:
            table_name = str(table.get("table_name", "")).lower()
            columns = table.get("columns", [])

            column_names = [
                str(column.get("column_name", "")).lower()
                for column in columns
                if isinstance(column, dict)
            ]

            header_score = self._score_table(
                table_name=table_name,
                column_names=column_names,
                keywords=header_keywords,
            )

            line_score = self._score_table(
                table_name=table_name,
                column_names=column_names,
                keywords=line_keywords,
            )

            if header_score > 0:
                header_candidates.append(
                    {
                        "table_name": table.get("table_name"),
                        "score": header_score,
                        "reason": "Table or columns look order-header related.",
                    }
                )

            if line_score > 0:
                line_candidates.append(
                    {
                        "table_name": table.get("table_name"),
                        "score": line_score,
                        "reason": "Table or columns look order-line related.",
                    }
                )

        header_candidates.sort(key=lambda item: item["score"], reverse=True)
        line_candidates.sort(key=lambda item: item["score"], reverse=True)

        return {
            "possible_order_header_tables": header_candidates[:10],
            "possible_order_line_tables": line_candidates[:10],
        }

    def _score_table(
        self,
        table_name: str,
        column_names: list[str],
        keywords: list[str],
    ) -> int:
        score = 0

        for keyword in keywords:
            if keyword in table_name:
                score += 3

            for column_name in column_names:
                if keyword in column_name:
                    score += 1

        return score

    def _mask_connection_string(self, connection_string: str) -> str:
        hidden_keywords = [
            "PWD=",
            "Password=",
            "PASSWORD=",
            "Pwd=",
            "Uid=",
            "UID=",
            "User ID=",
            "USER ID=",
        ]

        masked = connection_string

        for keyword in hidden_keywords:
            if keyword in masked:
                start = masked.find(keyword) + len(keyword)
                end = masked.find(";", start)

                if end == -1:
                    end = len(masked)

                masked = masked[:start] + "****" + masked[end:]

        return masked