"""
file_processing_pipeline.py

High-level file processing pipeline for the Modula WMS Data Integration Agent.

Pipeline Flow:

Customer File
    ↓
Profile Detection or Explicit Profile Selection
    ↓
If No Profile Exists: AI Customer Onboarding
    ↓
Profile Loading
    ↓
Parser Selection
    ↓
Field Mapping
    ↓
Internal Order Format
    ↓
Workflow Runner
    ↓
Validation
    ↓
Decision Engine
    ↓
XML Export
    ↓
Transaction History
"""

from pathlib import Path
from typing import Any, Dict, List

from src.ai.customer_onboarding_agent import CustomerOnboardingAgent
from src.parsing.parser_factory import ParserFactory
from src.profiles.profile_detector import ProfileDetector
from src.profiles.profile_loader import ProfileLoader
from src.workflow.workflow_runner import WorkflowRunner


class FileProcessingPipeline:
    """
    Coordinates file-level processing for customer order data.
    """

    def __init__(self):
        self.profile_detector = ProfileDetector()
        self.profile_loader = ProfileLoader()
        self.workflow_runner = WorkflowRunner()
        self.customer_onboarding_agent = CustomerOnboardingAgent()

    def process_transformed_orders(
        self,
        orders: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Process already-transformed orders.
        """

        return self.workflow_runner.run(orders)

    def process_file(
        self,
        file_path: str,
        profile_path: str | None = None,
    ) -> Dict[str, Any]:
        """
        Process a customer input file.

        If profile_path is provided, the pipeline uses that exact profile.
        Otherwise, it detects an existing profile or starts AI onboarding.
        """

        try:
            profile_name = None

            if profile_path:
                profile = self.profile_loader.load_profile_from_path(profile_path)
                profile_name = self._profile_name_from_path(profile_path)
            else:
                profile_name = self._get_or_create_profile(file_path)
                profile = self.profile_loader.load_profile(profile_name)

            parser = ParserFactory.get_parser(file_path)

            orders = parser.parse(
                file_path,
                profile=profile,
            )

            return self.workflow_runner.run(
                orders,
                metadata={
                    "source_file": file_path,
                    "orders_loaded": len(orders),
                    "parser_used": type(parser).__name__,
                    "profile_used": profile_name,
                    "profile_path": profile_path,
                },
            )

        except Exception as error:
            return {
                "status": "error",
                "source_file": file_path,
                "error_message": str(error),
                "orders_loaded": 0,
                "decision": {
                    "action": "stop_processing",
                    "reason": "Pipeline error occurred.",
                },
                "export_result": {
                    "status": "skipped",
                    "output_path": None,
                    "orders_exported": 0,
                },
            }

    def _get_or_create_profile(
        self,
        file_path: str,
    ) -> str:
        """
        Detect an existing profile or create a new one using AI.
        """

        try:
            return self.profile_detector.detect_profile(file_path)

        except ValueError:
            print("\nNo matching customer profile found.")
            print("Starting AI-assisted customer onboarding.")

            profile_name = input(
                "Enter a name for the new customer profile: "
            ).strip()

            onboarding_result = self.customer_onboarding_agent.onboard_customer(
                file_path=file_path,
                profile_name=profile_name,
            )

            if onboarding_result["status"] != "success":
                raise ValueError("Customer onboarding was cancelled.")

            return onboarding_result["save_result"]["profile_name"]

    def _profile_name_from_path(self, profile_path: str) -> str:
        """
        Extract profile name from a profile file path.
        """

        return Path(profile_path).stem