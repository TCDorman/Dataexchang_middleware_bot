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
            {"item": "XYZ789", "quantity": 15000},
        ],
    },
    {
        "order_id": "ORD-1001",
        "lines": [
            {"quantity": 2},
        ],
    },
]

report = workflow.run_validation_report(orders)

print(formatter.format_validation_report(report))