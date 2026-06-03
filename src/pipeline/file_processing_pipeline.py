"""
file_processing_pipeline.py

High-level file processing pipeline for the Modula WMS Data Integration Agent.

Pipeline Flow:

Customer File
    ↓
Profile Detection
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
        """
        Initialize pipeline components.
        """

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

        Args:
            orders: Internal order dictionaries.

        Returns:
            Full workflow result.
        """

        return self.workflow_runner.run(orders)

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process a customer input file.

        If no matching profile exists, the pipeline starts
        AI-assisted customer onboarding.

        Args:
            file_path: Path to the customer file.

        Returns:
            Full workflow result or clean error result.
        """

        try:
            # Step 1: Detect an existing profile or create one with AI.
            profile_name = self._get_or_create_profile(file_path)

            # Step 2: Load the selected/generated customer profile.
            profile = self.profile_loader.load_profile(profile_name)

            # Step 3: Select the correct parser based on file type.
            parser = ParserFactory.get_parser(file_path)

            # Step 4: Parse file using the selected customer profile.
            orders = parser.parse(
                file_path,
                profile=profile,
            )

            # Step 5: Run the parsed orders through the workflow.
            return self.workflow_runner.run(
                orders,
                metadata={
                    "source_file": file_path,
                    "orders_loaded": len(orders),
                    "parser_used": type(parser).__name__,
                    "profile_used": profile_name,
                },
            )

        except Exception as error:
            # Return a clean error response instead of crashing the app.
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

        Args:
            file_path: Customer input file.

        Returns:
            Profile name.
        """

        try:
            # Try to detect an existing customer profile first.
            return self.profile_detector.detect_profile(file_path)

        except ValueError:
            # If no profile exists, start the AI onboarding flow.
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
                raise ValueError(
                    "Customer onboarding was cancelled."
                )

            return onboarding_result["save_result"]["profile_name"]