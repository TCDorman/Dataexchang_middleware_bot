"""
sql_query_builder.py

Builds safe SQL SELECT queries for SQL integration workflows.

Important:
- Values must be passed through query params.
- Do not insert user-provided values directly into WHERE values.
"""


class SQLQueryBuilder:
    """
    Builds SELECT queries from SQL source configuration and field mappings.
    """

    def build_select_query(
        self,
        source_config: dict,
        field_mapping: dict[str, str],
    ) -> dict:
        source_table = source_config["source_table"]
        selected_columns = source_config.get("selected_columns") or []
        join_clause = source_config.get("join_clause")
        filter_clause = source_config.get("filter_clause")

        select_columns = self._build_select_columns(
            selected_columns=selected_columns,
            field_mapping=field_mapping,
        )

        sql_parts = [
            "SELECT",
            ", ".join(select_columns),
            f"FROM {source_table}",
        ]

        if join_clause:
            sql_parts.append(join_clause)

        if filter_clause:
            sql_parts.append(f"WHERE {filter_clause}")

        sql = "\n".join(sql_parts)

        return {
            "sql": sql,
            "params": source_config.get("params", []),
        }

    def _build_select_columns(
        self,
        selected_columns: list[str],
        field_mapping: dict[str, str],
    ) -> list[str]:
        if selected_columns:
            return selected_columns

        columns = []

        for wms_field, source_column in field_mapping.items():
            if not source_column:
                continue

            columns.append(f"{source_column} AS {wms_field}")

        if not columns:
            columns.append("*")

        return columns