from src.ai.profile_generation_agent import ProfileGenerationAgent

print("Starting AI profile generation test...")

agent = ProfileGenerationAgent()

print("Agent created. Sending headers to OpenAI...")

profile = agent.generate_profile(
    [
        "PO_NUM",
        "CUSTOMER_NAME",
        "PART_NUMBER",
        "REQUESTED_QTY",
    ]
)

print("AI returned profile:")
print(profile)