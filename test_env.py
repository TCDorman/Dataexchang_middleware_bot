from dotenv import load_dotenv
import os

load_dotenv()

print("DEMO_API_KEY =", os.getenv("DEMO_API_KEY"))