"""
test_workflow_runner.py

Manual test for the full WorkflowRunner.

This verifies that validation, decision-making, XML export,
and transaction history all work together.
"""

from src.workflow.report_formatter import ReportFormatter
from src.workflow.workflow_runner import WorkflowRunner

runner = WorkflowRunner()
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

result = runner.run(orders)

print("Workflow Status:", result["status"])
print("Decision:", result["decision"])
print("Export Result:", result["export_result"])
print("History Record:", result["history_record"])

print()
print(formatter.format_validation_report(result["validation_report"]))