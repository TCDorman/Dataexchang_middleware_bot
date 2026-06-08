"""
==================================================
AI Profile Save Test
==================================================

Purpose:
    Tests whether an AI-generated customer profile
    can be saved into configs/customers.
"""

# ==================================================
# Imports
# ==================================================

from src.ai.profile_generation_agent import ProfileGenerationAgent
from src.profiles.profile_saver import ProfileSaver


# ==================================================
# Test AI Profile Save
# ==================================================

headers = [
    "OrderNumber",
    "Customer",
    "PartNumber",
    "Qty",
]

profile_generator = ProfileGenerationAgent()
profile_saver = ProfileSaver()

profile = profile_generator.generate_profile(headers)

result = profile_saver.save_profile(
    profile_name="ai_generated_test_customer",
    profile=profile,
)

print(result)
print(profile)