from src.ai.openai_client import OpenAIClient

client = OpenAIClient()

response = client.ask(
    "Reply with exactly: OpenAI connection successful"
)

print(response)