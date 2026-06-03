"""
test_xml_export_manager.py

Manual test for the XML export manager.
"""

from src.output.xml_export_manager import XmlExportManager

export_manager = XmlExportManager()

orders = [
    {
        "order_id": "ORD-1001",
        "customer_name": "Ford",
        "lines": [
            {"item": "ABC123", "quantity": 5},
            {"item": "XYZ789", "quantity": 2},
        ],
    }
]

result = export_manager.export_orders(orders)

print(result)