"""
==================================================
API Onboarding Workflow Test
==================================================
"""

from src.connectors.api_onboarding_workflow import (
    ApiOnboardingWorkflow,
)

documentation = """
Customer: Demo ERP

Base URL:
https://api.demo-erp.com/v1

Authentication:
Use an API key in the Authorization header.

Orders Endpoint:
GET /orders

Sample Response:
{
    "orders": [
        {
            "orderNo": "ORD-1001",
            "description": "Customer order",
            "type": "PICK",
            "items": [
                {
                    "sku": "ABC123",
                    "qty": 5
                }
            ]
        }
    ]
}
"""

workflow = ApiOnboardingWorkflow()

result = workflow.onboard_from_text(documentation)

print(result)