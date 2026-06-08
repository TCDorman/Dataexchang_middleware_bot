"""
==================================================
Full Customer Onboarding Test
==================================================

Purpose:
    Tests the complete AI onboarding flow:

    CSV file
    -> read headers
    -> generate AI profile
    -> review mapping
    -> approve profile
    -> save profile
"""

# ==================================================
# Imports
# ==================================================

from src.ai.customer_onboarding_agent import CustomerOnboardingAgent


# ==================================================
# Run Full Onboarding Test
# ==================================================

agent = CustomerOnboardingAgent()

result = agent.onboard_customer(
    file_path="data/sample_files/customer_order_headers.csv",
    profile_name="ai_onboarded_customer",
)

print(result)