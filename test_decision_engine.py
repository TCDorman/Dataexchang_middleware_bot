"""
test_decision_engine.py

Manual test for the Decision Engine.
"""

from src.workflow.processing_workflow import ProcessingWorkflow
from src.workflow.decision_engine import DecisionEngine

workflow = ProcessingWorkflow()
decision_engine = DecisionEngine()

orders = [
    {
        "order_id": "ORD-1001",
        "customer_name": "Ford",
        "lines": [
            {"item": "ABC123", "quantity": 5},
        ],
    }
]

workflow_result = workflow.process_transformed_orders(orders)

decision = decision_engine.evaluate(workflow_result)

print("Workflow Result:")
print(workflow_result)

print()
print("Decision:")
print(decision)