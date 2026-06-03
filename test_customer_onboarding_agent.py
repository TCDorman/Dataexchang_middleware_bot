from src.ai.customer_onboarding_agent import (
    CustomerOnboardingAgent
)

agent = CustomerOnboardingAgent()

result = pipeline.process_file(
    "data/customer_input/brand_new_customer.csv"
)

print("\nResult:")
print(result)