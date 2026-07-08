"""
==================================================
API Onboarding Workflow
==================================================

Purpose:
    Runs the full API onboarding workflow from
    customer API documentation to generated assets.

Workflow:
    1. Read API documentation text
    2. Analyze documentation with AI
    3. Generate API config and starter package
    4. Return full onboarding result
"""

# ==================================================
# Imports
# ==================================================

from pathlib import Path
from typing import Dict

from src.connectors.api_documentation_analyzer import (
    ApiDocumentationAnalyzer,
)
from src.connectors.api_integration_generator import (
    ApiIntegrationGenerator,
)


# ==================================================
# API Onboarding Workflow
# ==================================================

class ApiOnboardingWorkflow:
    """
    Coordinates API documentation analysis and
    integration package generation.
    """

    def __init__(self):
        """
        Initialize workflow components.
        """

        self.documentation_analyzer = ApiDocumentationAnalyzer()
        self.integration_generator = ApiIntegrationGenerator()

    def onboard_from_text(
        self,
        documentation_text: str,
    ) -> Dict:
        """
        Onboard an API integration from raw documentation text.
        """

        analysis_result = (
            self.documentation_analyzer.analyze_documentation(
                documentation_text
            )
        )

        generation_result = self.integration_generator.generate(
            analysis_result
        )

        return {
            "status": "success",
            "analysis_result": analysis_result,
            "generation_result": generation_result,
        }

    def onboard_from_file(
        self,
        documentation_file_path: str,
    ) -> Dict:
        """
        Onboard an API integration from a documentation file.
        """

        path = Path(documentation_file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"API documentation file does not exist: {path}"
            )

        documentation_text = path.read_text(
            encoding="utf-8"
        )

        return self.onboard_from_text(
            documentation_text
        )