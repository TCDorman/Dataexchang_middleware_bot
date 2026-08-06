"""
setup_sql_odbc.py

Customer-friendly SQL / ODBC setup utility.

Run from the generated package folder:
    python setup_sql_odbc.py

Or double-click:
    setup_database.bat

This script updates only the "sql" section of config.json.
"""

import json
import sqlite3
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = PACKAGE_DIR / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing config.json: {CONFIG_PATH}")

    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def save_config(config: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=4)


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    default_label = "Y/n" if default else "y/N"

    while True:
        value = input(f"{prompt} [{default_label}]: ").strip().lower()

        if not value:
            return default

        if value in ["y", "yes"]:
            return True

        if value in ["n", "no"]:
            return False

        print("Please enter y or n.")


def ask_text(prompt: str, default: str = "") -> str:
    if default:
        value = input(f"{prompt} [{default}]: ").strip()
        return value or default

    return input(f"{prompt}: ").strip()


def ask_int(prompt: str, default: int) -> int:
    while True:
        value = input(f"{prompt} [{default}]: ").strip()

        if not value:
            return default

        try:
            return int(value)
        except ValueError:
            print("Please enter a whole number.")


def ask_json_object(prompt: str, default: dict | None = None) -> dict:
    default = default or {}

    print(prompt)
    print("Leave blank for {}.")

    while True:
        value = input("> ").strip()

        if not value:
            return default

        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as error:
            print(f"Invalid JSON: {error}")
            continue

        if not isinstance(parsed, dict):
            print("Please enter a JSON object, for example: {\"order_id\": \"OrderNumber\"}")
            continue

        return parsed


def resolve_package_path(path_value: str) -> Path:
    path = Path(path_value)

    if path.is_absolute():
        return path

    return PACKAGE_DIR / path


def test_sql_connection(sql_config: dict) -> bool:
    database_type = str(sql_config.get("database_type", "sqlite")).lower()
    connection_string = sql_config.get("connection_string", "")
    timeout = int(sql_config.get("timeout_seconds", 30))

    if not connection_string:
        print("Connection string is blank; cannot test connection.")
        return False

    try:
        if database_type == "sqlite":
            db_path = resolve_package_path(connection_string)
            db_path.parent.mkdir(parents=True, exist_ok=True)

            with sqlite3.connect(str(db_path), timeout=timeout) as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT 1 AS connection_test")
                result = cursor.fetchone()

            print(f"SQLite connection test succeeded: {result[0]}")
            print(f"Database path: {db_path}")
            return True

        if database_type in ["odbc", "sql_server"]:
            try:
                import pyodbc
            except ImportError:
                print("pyodbc is not installed. Install it with: pip install pyodbc")
                return False

            connection = pyodbc.connect(connection_string, timeout=timeout)
            cursor = connection.cursor()
            cursor.execute("SELECT 1 AS connection_test")
            result = cursor.fetchone()
            cursor.close()
            connection.close()

            print(f"ODBC connection test succeeded: {result[0]}")
            return True

        print(f"Unsupported database_type: {database_type}")
        return False

    except Exception as error:
        print(f"SQL connection test failed: {error}")
        return False


def create_sqlite_demo_database(sql_config: dict) -> None:
    database_type = str(sql_config.get("database_type", "sqlite")).lower()

    if database_type != "sqlite":
        print("Demo database creation is only available for SQLite.")
        return

    db_path = resolve_package_path(sql_config.get("connection_string", "runtime/sql/customer_orders.db"))
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(str(db_path)) as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS orders_to_modula (
                order_id TEXT NOT NULL,
                customer_name TEXT,
                item TEXT NOT NULL,
                quantity REAL NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS order_confirmations (
                order_id TEXT,
                item TEXT,
                quantity TEXT,
                operation_type TEXT,
                exported_at TEXT
            )
            """
        )

        cursor.execute("DELETE FROM orders_to_modula")

        cursor.executemany(
            """
            INSERT INTO orders_to_modula (
                order_id,
                customer_name,
                item,
                quantity
            ) VALUES (?, ?, ?, ?)
            """,
            [
                ("PO10001", "Brawl Industries", "BRG-100", 10),
                ("PO10001", "Brawl Industries", "CBL-100", 5),
                ("PO10002", "Brawl Industries", "CBL-200", 8),
            ],
        )

        connection.commit()

    print(f"SQLite demo database created/updated: {db_path}")
    print("Demo import table: orders_to_modula")
    print("Demo export table: order_confirmations")


def configure_sql(config: dict) -> dict:
    sql_config = dict(config.get("sql", {}) or {})

    print("=" * 70)
    print("SQL / ODBC SETUP")
    print("=" * 70)
    print("This setup updates only config.json -> sql.")
    print("SQLite is recommended first for testing. Use ODBC later for SQL Server.")
    print("=" * 70)

    import_enabled = ask_yes_no(
        "Enable SQL import? Database -> Modula",
        bool(sql_config.get("import_enabled", False)),
    )

    export_enabled = ask_yes_no(
        "Enable SQL export? Modula -> Database",
        bool(sql_config.get("export_enabled", False)),
    )

    sql_config["enabled"] = import_enabled or export_enabled
    sql_config["import_enabled"] = import_enabled
    sql_config["export_enabled"] = export_enabled

    database_type = ask_text(
        "Database type: sqlite, odbc, or sql_server",
        sql_config.get("database_type", "sqlite"),
    ).lower()

    if database_type not in ["sqlite", "odbc", "sql_server"]:
        print("Unsupported database type entered; defaulting to sqlite.")
        database_type = "sqlite"

    sql_config["database_type"] = database_type

    default_connection = sql_config.get(
        "connection_string",
        "runtime/sql/customer_orders.db",
    )

    sql_config["connection_string"] = ask_text(
        "Connection string or SQLite database path",
        default_connection,
    )

    if import_enabled:
        sql_config["import_query"] = ask_text(
            "Import SELECT query",
            sql_config.get("import_query", "SELECT * FROM orders_to_modula"),
        )

        sql_config["processed_key_column"] = ask_text(
            "Processed key column used to prevent duplicate imports",
            sql_config.get("processed_key_column", "order_id"),
        )

    if export_enabled:
        sql_config["export_table"] = ask_text(
            "Export confirmation table",
            sql_config.get("export_table", "order_confirmations"),
        )

    sql_config["field_mapping"] = ask_json_object(
        "Optional SQL field mapping as JSON object",
        sql_config.get("field_mapping", {}),
    )

    sql_config["poll_interval_seconds"] = ask_int(
        "SQL import poll interval in seconds",
        int(sql_config.get("poll_interval_seconds", 60)),
    )

    sql_config["timeout_seconds"] = ask_int(
        "Database timeout in seconds",
        int(sql_config.get("timeout_seconds", 30)),
    )

    config["sql"] = sql_config
    return config


def main() -> None:
    config = load_config()
    config = configure_sql(config)

    sql_config = config.get("sql", {})

    print()
    if ask_yes_no("Test SQL connection now?", True):
        test_sql_connection(sql_config)

    if sql_config.get("database_type") == "sqlite" and ask_yes_no(
        "Create/update SQLite demo tables and sample orders?",
        True,
    ):
        create_sqlite_demo_database(sql_config)

    save_config(config)

    print()
    print("SQL / ODBC settings saved to config.json.")
    print("Setup complete. You can now run start.bat or always_on_runtime.py.")


if __name__ == "__main__":
    main()
