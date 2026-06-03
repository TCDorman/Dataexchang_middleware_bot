"""
customer_onboarding_agent.py

AI-powered customer onboarding workflow.

This agent:

1. Reads unknown CSV headers
2. Generates a customer profile using OpenAI
3. Shows a human-friendly mapping review
4. Warns about low-confidence mappings
5. Requests approval
6. Saves the profile if approved
"""

import csv
import json
from typing import Dict, List

from src.ai.profile_generation_agent import ProfileGenerationAgent
from src.profiles.profile_saver import ProfileSaver


class CustomerOnboardingAgent:
    """
    AI-powered customer onboarding workflow.
    """

    def __init__(self):
        """
        Initialize onboarding components.
        """

        self.profile_generation_agent = ProfileGenerationAgent()
        self.profile_saver = ProfileSaver()

    def onboard_customer(
        self,
        file_path: str,
        profile_name: str,
    ) -> Dict:
        """
        Generate, review, approve, and save a customer profile.

        Args:
            file_path: Customer CSV file.
            profile_name: Name for the new customer profile.

        Returns:
            Result dictionary.
        """

        headers = self._read_headers(file_path)

        generated_profile = self.profile_generation_agent.generate_profile(
            headers
        )

        self._print_mapping_review(generated_profile)

        approval = input(
            "\nApprove and save this profile? (y/n): "
        ).strip().lower()

        if approval != "y":
            return {
                "status": "cancelled",
                "reason": "User rejected generated profile.",
            }

        save_result = self.profile_saver.save_profile(
            profile_name,
            generated_profile,
        )

        return {
            "status": "success",
            "profile": generated_profile,
            "save_result": save_result,
        }

    def _read_headers(
        self,
        file_path: str,
    ) -> List[str]:
        """
        Read CSV headers.

        Args:
            file_path: CSV file.

        Returns:
            List of headers.
        """

        with open(
            file_path,
            mode="r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.reader(file)
            headers = next(reader)

        return headers

    def _print_mapping_review(
        self,
        profile: Dict,
    ) -> None:
        """
        Print a human-friendly mapping review.

        Args:
            profile: AI-generated customer profile.
        """

        field_mapping = profile.get("field_mapping", {})
        confidence = profile.get("mapping_confidence", {})
        notes = profile.get("mapping_notes", {})

        print("\n" + "=" * 60)
        print("AI-GENERATED CUSTOMER PROFILE REVIEW")
        print("=" * 60)

        print("\nCustomer Name:")
        print(profile.get("customer_name", "Unknown Customer"))

        print("\nDetected Headers:")
        for header in profile.get("header_signature", []):
            print(f"  - {header}")

        print("\nSuggested Field Mappings:")
        for source_field, target_field in field_mapping.items():
            score = confidence.get(source_field, "N/A")
            note = notes.get(source_field, "")

            print(
                f"  {source_field} -> {target_field} "
                f"(confidence: {score}%)"
            )

            if note:
                print(f"      Note: {note}")

        low_confidence_mappings = self._get_low_confidence_mappings(
            profile
        )

        if low_confidence_mappings:
            print("\nWARNING: Low-confidence mappings detected.")
            print("Review these carefully before approving:")

            for mapping in low_confidence_mappings:
                print(
                    f"  - {mapping['source_field']} -> "
                    f"{mapping['target_field']} "
                    f"({mapping['confidence']}%)"
                )

        print("\nRaw Profile JSON:")
        print(json.dumps(profile, indent=4))

        print("=" * 60)

    def _get_low_confidence_mappings(
        self,
        profile: Dict,
        threshold: int = 80,
    ) -> List[Dict]:
        """
        Identify mappings below the confidence threshold.

        Args:
            profile: AI-generated profile.
            threshold: Minimum acceptable confidence score.

        Returns:
            List of low-confidence mapping records.
        """

        field_mapping = profile.get("field_mapping", {})
        confidence = profile.get("mapping_confidence", {})

        low_confidence = []

        for source_field, target_field in field_mapping.items():
            score = confidence.get(source_field)

            if isinstance(score, int) and score < threshold:
                low_confidence.append(
                    {
                        "source_field": source_field,
                        "target_field": target_field,
                        "confidence": score,
                    }
                )

        return low_confidence