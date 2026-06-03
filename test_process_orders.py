"""
test_process_orders.py

Tests the main workflow entry point.

This simulates what the CLI and future desktop application
will eventually call after data transformation is complete.
"""

from src.workflow.processing_workflow import ProcessingWorkflow
from src.workflow.report_formatter import ReportFormatter

workflow = ProcessingWorkflow()
formatter = ReportFormatter()

orders = [
    {
        "order_id": "ORD-1001",
        "customer_name": "Ford",
        "lines": [
            {"item": "ABC123", "quantity": 5},
        ],
    }
]

result = workflow.process_transformed_orders(orders)

print("Workflow Status:", result["status"])
print("Orders Processed:", result["orders_processed"])

print()
print(
    formatter.format_validation_report(
        result["validation_report"]
    )
)