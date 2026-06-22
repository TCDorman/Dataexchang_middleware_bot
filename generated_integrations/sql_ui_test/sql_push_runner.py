"""
sql_push_runner.py

Generated SQL push runner for SQL UI Test.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.connectors.db_connector import DBConnector


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_records(source_path: str) -> list[dict]:
    path = Path(source_path)

    if path.suffix.lower() == ".json":
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            return data.get("records", [data])

    if path.suffix.lower() == ".csv":
        with open(path, "r", encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))

    raise ValueError(f"Unsupported source file type: {path.suffix}")


def build_insert_sql(table_name: str, columns: list[str]) -> str:
    column_list = ", ".join(columns)
    placeholders = ", ".join(["?"] * len(columns))

    return f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})"


def run_push(config: dict, dry_run: bool = False) -> dict:
    connection_string = config["connection_string"]
    database_type = config.get("database_type", "sqlite")
    source_path = config["source_path"]
    target_table = config["target_table"]
    field_mapping = config["field_mapping"]

    records = load_records(source_path)

    insert_columns = list(field_mapping.values())
    insert_sql = build_insert_sql(target_table, insert_columns)

    prepared_rows = []

    for record in records:
        row_values = []

        for source_field in field_mapping.keys():
            row_values.append(record.get(source_field))

        prepared_rows.append(row_values)

    result = {
        "status": "dry_run" if dry_run else "success",
        "customer_name": "SQL UI Test",
        "target_table": target_table,
        "records_loaded": len(records),
        "records_prepared": len(prepared_rows),
        "insert_sql": insert_sql,
    }

    if dry_run:
        result["preview_rows"] = prepared_rows
        return result

    inserted_count = 0

    with DBConnector(
        connection_string=connection_string,
        database_type=database_type,
    ) as db:
        for row_values in prepared_rows:
            db.execute(insert_sql, row_values)
            inserted_count += 1

    result["records_inserted"] = inserted_count
    return result


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--config", required=True)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    config = load_config(args.config)

    result = run_push(
        config=config,
        dry_run=args.dry_run,
    )

    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
