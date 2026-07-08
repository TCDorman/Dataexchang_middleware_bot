"""
sql_config_generator.py

Generates JSON config files for SQL pull and push runners.
"""

import json
from pathlib import Path
from typing import Any


class SQLConfigGenerator:
    """
    Generates SQL integration config files.
    """

    def generate_pull_config(
        self,
        output_folder: str,
        connection_string: str,
        query: str,
        database_type: str = "sqlite",
        config_name: str = "sql_pull_config.json",
        output_path: str = "data/sql_pull_output/sql_pull_result.json",
    ) -> dict:
        config_path = Path(output_folder) / config_name
        config_path.parent.mkdir(parents=True, exist_ok=True)

        config = {
            "connection_string": connection_string,
            "database_type": database_type,
            "query": query,
            "output_path": output_path,
        }

        self._write_json(config_path, config)

        return {
            "status": "success",
            "config_type": "sql_pull",
            "config_path": str(config_path),
        }

    def generate_push_config(
        self,
        output_folder: str,
        connection_string: str,
        source_path: str,
        target_table: str,
        field_mapping: dict[str, str],
        database_type: str = "sqlite",
        config_name: str = "sql_push_config.json",
    ) -> dict:
        config_path = Path(output_folder) / config_name
        config_path.parent.mkdir(parents=True, exist_ok=True)

        config = {
            "connection_string": connection_string,
            "database_type": database_type,
            "source_path": source_path,
            "target_table": target_table,
            "field_mapping": field_mapping,
        }

        self._write_json(config_path, config)

        return {
            "status": "success",
            "config_type": "sql_push",
            "config_path": str(config_path),
        }

    def _write_json(
        self,
        path: Path,
        data: dict[str, Any],
    ) -> None:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)