"""
validation_explanation_agent.py

Uses OpenAI to explain validation failures in plain English.

This helps users understand why a file failed and what they should fix.
"""

from typing import Any, Dict

from src.ai.openai_client import OpenAIClient


class ValidationExplanationAgent:
    """
    Generates human-readable explanations for validation failures.
    """

    def __init__(self):
        """
        Initialize AI client.
        """

        self.openai_client = OpenAIClient()

    def explain_validation_result(
        self,
        workflow_result: Dict[str, Any],
    ) -> str:
        """
        Explain a workflow validation result.

        Args:
            workflow_result: Result returned by the workflow runner.

        Returns:
            Plain-English explanation.
        """

        validation_report = workflow_result.get("validation_report", {})
        decision = workflow_result.get("decision", {})
        export_result = workflow_result.get("export_result", {})

        prompt = f"""
You are helping a non-technical warehouse operations user understand
why an ERP/WMS integration file did not process successfully.

Explain the issue clearly and briefly.

Use this structure:

Summary:
Likely Cause:
Suggested Fix:

Workflow Status:
{workflow_result.get("status")}

Decision:
{decision}

Validation Report:
{validation_report}

Export Result:
{export_result}

Rules:
- Do not use technical jargon unless necessary.
- Be specific.
- Do not invent data that is not present.
- If the file passed validation, say that no fix is needed.
"""

        return self.openai_client.ask(prompt)