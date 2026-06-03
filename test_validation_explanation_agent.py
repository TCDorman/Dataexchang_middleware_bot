"""
test_validation_explanation_agent.py

Tests AI explanation for a failed validation result.
"""

from src.ai.validation_explanation_agent import ValidationExplanationAgent
from src.workflow.workflow_runner import WorkflowRunner


runner = WorkflowRunner()
agent = ValidationExplanationAgent()

orders = [
    {
        "order_id": "BAD-1001",
        "customer_name": "",
        "lines": [
            {
                "item": "",
                "quantity": 15000,
            }
        ],
    },
    {
        "order_id": "BAD-1001",
        "customer_name": "",
        "lines": [
            {
                "item": "",
                "quantity": "abc",
            }
        ],
    },
]

result = runner.run(orders)

explanation = agent.explain_validation_result(result)

print(explanation)