"""
sql_pull_script_generator.py

Generates standalone SQL pull scripts for customer integrations.
"""

from pathlib import Path


class SQLPullScriptGenerator:
    """
    Generates a Python script that pulls records from a SQL database.
    """

    def generate(
        self,
        customer_name: str,
        output_folder: str,
        script_name: str = "sql_pull_runner.py",
    ) -> dict:
        output_path = Path(output_folder) / script_name
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as file:
            file.write(self._build_script(customer_name))

        return {
            "status": "success",
            "customer_name": customer_name,
            "script_path": str(output_path),
        }

    def _build_script(
        self,
        customer_name: str,
    ) -> str:
        return f'''"""
sql_pull_runner.py

Generated SQL pull runner for {customer_name}.
"""

import argparse
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


def run_pull(config: dict, dry_run: bool = False) -> dict:
    connection_string = config["connection_string"]
    database_type = config.get("database_type", "sqlite")
    query = config["query"]
    output_path = config["output_path"]

    with DBConnector(
        connection_string=connection_string,
        database_type=database_type,
    ) as db:
        rows = db.fetch_all(query)

    result = {{
        "status": "dry_run" if dry_run else "success",
        "customer_name": "{customer_name}",
        "records_pulled": len(rows),
        "data": rows,
    }}

    if not dry_run:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(result, file, indent=4)

        result["output_path"] = str(output_file)

    return result


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--config", required=True)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    config = load_config(args.config)

    result = run_pull(
        config=config,
        dry_run=args.dry_run,
    )

    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
'''