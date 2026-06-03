"""
test_transaction_history.py

Manual test for local transaction history logging.

This simulates saving the result of a workflow run.
"""

from src.storage.transaction_history import TransactionHistory
from src.workflow.processing_workflow import ProcessingWorkflow

workflow = ProcessingWorkflow()
history = TransactionHistory()

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

saved_record = history.record_run(result)

print("Saved History Record:")
print(saved_record)

print()
print("All History:")
print(history.get_history())