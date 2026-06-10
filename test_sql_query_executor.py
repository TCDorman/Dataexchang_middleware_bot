from src.connectors.sql_query_executor import SqlQueryExecutor

executor = SqlQueryExecutor()

rows = executor.execute_query(
    connection_string=(
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=localhost\\SQLEXPRESS;"
        "Database=master;"
        "Trusted_Connection=yes;"
    ),
    query="""
        SELECT TOP 5
        name
        FROM sys.databases
    """,
)

print(rows)