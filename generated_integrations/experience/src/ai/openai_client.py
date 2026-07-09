"""
openai_client.py

Centralized OpenAI client for the Modula Integration Agent.

All AI-powered components should use this client rather than
creating their own OpenAI connections.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI


class OpenAIClient:
    """
    Wrapper around the OpenAI SDK.
    """

    def __init__(self):
        """
        Initialize OpenAI client.
        """

        load_dotenv()

        api_key = os.getenv("OPENAI_API_KEY")


        if not api_key:
            raise ValueError(
                "\nOPENAI_API_KEY not found.\n"
                "Create a .env file in the project root and add:\n\n"
                "OPENAI_API_KEY=your_api_key_here\n"
            )

        self.client = OpenAI(
            api_key=api_key,
        )

    def ask(
        self,
        prompt: str,
        model: str = "gpt-4.1-mini",
    ) -> str:
        """
        Send a prompt to OpenAI and return text response.

        Args:
            prompt: User prompt.
            model: OpenAI model name.

        Returns:
            Response text.
        """

        response = self.client.responses.create(
            model=model,
            input=prompt,
        )

        return response.output_text