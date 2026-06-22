# tests/test_live_rest_api_workflow.py

from agents.integration_workflow_manager import IntegrationWorkflowManager


manager = IntegrationWorkflowManager()

result = manager.run_live_rest_api_workflow(
    base_url="https://jsonplaceholder.typicode.com",
    endpoint="/posts/1",
)

print("LIVE REST API WORKFLOW TEST")
print("=" * 60)
print(result)