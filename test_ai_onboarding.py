import json

from agents.integration_package_generator import generate_integration_package_from_file


result = generate_integration_package_from_file(
    customer_name="Tesla",
    source_type="csv",
    file_path="data/customer_input/weird_customer.csv",
)

print(json.dumps(result, indent=4))