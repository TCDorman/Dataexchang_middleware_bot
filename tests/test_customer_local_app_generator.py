"""
test_customer_local_app_generator.py

Simple test for generating a customer-specific local agent.
"""

from agents.customer_local_app_generator import generate_customer_local_app
import json


def main():
    result = generate_customer_local_app(
        customer_name="Ford",
        customer_profile_path="configs/customers/ford_profile.json",
        source_type="file",
    )

    print("CUSTOMER LOCAL APP GENERATION COMPLETE")
    print("=" * 60)
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()