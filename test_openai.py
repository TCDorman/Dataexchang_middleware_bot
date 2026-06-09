from src.ai.openai_client import OpenAIClient


client = OpenAIClient()

response = client.ask(
    prompt="Reply with exactly: OpenAI connected successfully."
)

print(response)