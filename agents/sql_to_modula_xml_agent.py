"""
sql_to_modula_xml_agent.py

End-to-end SQL-to-XML workflow using SQL-style rows and the existing
XmlExportManager.
"""

from src.output.xml_export_manager import XmlExportManager
from src.parsing.sql_order_parser import SqlOrderParser


def generate_modula_xml_from_sql_test_rows(
    profile_path: str,
) -> dict:
    test_rows = [
        {
            "OrderID": 1001,
            "CustomerName": "Ford",
            "ShipToName": "Ford Plant A",
            "ShipToAddress": "123 Assembly Rd",
            "ItemNumber": "ABC123",
            "Quantity": 5,
            "LocationCode": "A1",
        },
        {
            "OrderID": 1001,
            "CustomerName": "Ford",
            "ShipToName": "Ford Plant A",
            "ShipToAddress": "123 Assembly Rd",
            "ItemNumber": "XYZ789",
            "Quantity": 2,
            "LocationCode": "B2",
        },
        {
            "OrderID": 1002,
            "CustomerName": "GM",
            "ShipToName": "GM Dock 4",
            "ShipToAddress": "500 Auto Way",
            "ItemNumber": "LMN456",
            "Quantity": 10,
            "LocationCode": "C3",
        },
    ]

    parser = SqlOrderParser()

    sql_orders = parser.parse_rows_from_profile(
        rows=test_rows,
        profile_path=profile_path,
    )

    exporter = XmlExportManager()
    export_result = exporter.export_orders(sql_orders)

    return {
        "status": "success",
        "source_type": "sql",
        "profile_path": profile_path,
        "orders_generated": len(sql_orders),
        "export": export_result,
    }