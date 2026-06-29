"""
sql_normalizer.py

Normalizes SQL schema inspection output into the shared ParsedSchema-style format.
"""


class SQLNormalizer:
    """
    Converts SchemaInspector table output into a normalized schema format.
    """

    def normalize_table_schema(
        self,
        table_schema: dict,
    ) -> dict:
        table_name = table_schema.get("table_name", "")
        columns = table_schema.get("columns", [])
        sample_rows = table_schema.get("sample_rows", [])

        fields = []

        for column in columns:
            column_name = column.get("name")

            fields.append(
                {
                    "name": column_name,
                    "source_name": column_name,
                    "type": column.get("type", "string"),
                    "nullable": column.get("nullable", True),
                    "primary_key": column.get("primary_key", False),
                    "sample_values": self._get_sample_values(
                        sample_rows=sample_rows,
                        column_name=column_name,
                    ),
                }
            )

        return {
            "source_type": "sql",
            "source_name": table_name,
            "fields": fields,
            "sample_count": len(sample_rows),
        }

    def normalize_database_schema(
        self,
        database_schema: dict,
    ) -> dict:
        return {
            "source_type": "sql",
            "database_type": database_schema.get("database_type"),
            "tables": [
                self.normalize_table_schema(table_schema)
                for table_schema in database_schema.get("tables", [])
            ],
        }

    def _get_sample_values(
        self,
        sample_rows: list[dict],
        column_name: str,
        max_values: int = 5,
    ) -> list:
        values = []

        for row in sample_rows:
            if column_name not in row:
                continue

            value = row.get(column_name)

            if value is None:
                continue

            if value not in values:
                values.append(value)

            if len(values) >= max_values:
                break

        return values