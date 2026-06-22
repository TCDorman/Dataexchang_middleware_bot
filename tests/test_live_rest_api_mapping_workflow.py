from agents.integration_workflow_manager import IntegrationWorkflowManager
from agents.openai_mapping_agent import infer_mapping_with_openai


manager = IntegrationWorkflowManager()

result = manager.run_live_rest_api_workflow(
    base_url="https://jsonplaceholder.typicode.com",
    endpoint="/posts/1",
)

fields = [
    field["source_field"]
    for field in result["normalized_schema"]["fields"]
]

mapping_result = infer_mapping_with_openai(fields)

print("LIVE REST API MAPPING TEST")
print("=" * 60)
print(mapping_result)