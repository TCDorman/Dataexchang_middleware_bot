"""
live_sql_to_modula_xml_agent.py

Production-style SQL-to-Modula XML workflow.

Flow:
1. Generate SQL query from customer SQL profile
2. Execute query against live SQL database
3. Parse returned rows into order dictionaries
4. Export orders to XML
"""

from agents.sql_query_generator import generate_sql_query_from_profile
from src.connectors.sql_query_executor import SqlQueryExecutor
from src.output.xml_export_manager import XmlExportManager
from src.parsing.sql_order_parser import SqlOrderParser


def generate_modula_xml_from_live_sql(
    connection_string: str,
    profile_path: str,
) -> dict:
    query_result = generate_sql_query_from_profile(profile_path)

    if query_result.get("status") != "success":
        return query_result

    query = query_result["query"]

    try:
        executor = SqlQueryExecutor()
        rows = executor.execute_query(
            connection_string=connection_string,
            query=query,
        )

        parser = SqlOrderParser()
        orders = parser.parse_rows_from_profile(
            rows=rows,
            profile_path=profile_path,
        )

        exporter = XmlExportManager()
        export_result = exporter.export_orders(orders)

        return {
            "status": "success",
            "source_type": "sql",
            "profile_path": profile_path,
            "query_output_path": query_result.get("output_path"),
            "rows_returned": len(rows),
            "orders_generated": len(orders),
            "export": export_result,
        }

    except Exception as error:
        return {
            "status": "error",
            "source_type": "sql",
            "message": "Live SQL to XML workflow failed.",
            "error": str(error),
            "profile_path": profile_path,
            "query_output_path": query_result.get("output_path"),
            "generated_query": query,
        }