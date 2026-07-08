"""
sql_discovery.py

Discovers SQL tables/views and builds a SQL source configuration.
"""

from typing import Any

from src.connectors.schema_inspector import SchemaInspector


class SQLDiscovery:
    """
    Helper for selecting source tables and recording configuration.
    """

    def __init__(self, inspector: SchemaInspector):
        self.inspector = inspector

    def list_sources(self) -> list[str]:
        """
        Return all discoverable tables/views.
        """
        return self.inspector.list_tables()

    def get_source_summary(
        self,
        table_name: str,
    ) -> dict[str, Any]:
        """
        Return metadata and sample rows for a table.
        """
        return self.inspector.inspect_table(table_name)

    def build_source_config(
        self,
        connection_string: str,
        source_table: str,
        selected_columns: list[str] | None = None,
        join_clause: str | None = None,
        filter_clause: str | None = None,
        direction: str = "pull",
    ) -> dict[str, Any]:
        """
        Build a reusable SQL source configuration.
        """

        return {
            "connection_string": connection_string,
            "source_table": source_table,
            "selected_columns": selected_columns or [],
            "join_clause": join_clause,
            "filter_clause": filter_clause,
            "direction": direction,
        }