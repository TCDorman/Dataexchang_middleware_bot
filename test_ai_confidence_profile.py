"""
test_ai_confidence_profile.py

Tests AI profile generation with confidence scores.
"""

import json

from src.ai.profile_generation_agent import ProfileGenerationAgent


agent = ProfileGenerationAgent()

profile = agent.generate_profile(
    [
        "SHIPMENT_REF",
        "BUYING_ORG",
        "MATERIAL_CODE",
        "ORDER_UNITS",
    ]
)

print(json.dumps(profile, indent=4))