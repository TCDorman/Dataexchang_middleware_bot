from agents.rest_to_modula_xml_agent import generate_modula_xml_from_rest_api


result = generate_modula_xml_from_rest_api(
    base_url="https://jsonplaceholder.typicode.com",
    endpoint="/posts/1",
    profile_path="configs/customers/demo_rest_customer_rest_profile.json",
)

print("REST TO MODULA XML TEST")
print("=" * 60)
print(result)