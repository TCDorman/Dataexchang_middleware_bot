"""
profile_detector.py

Detects customer profiles dynamically using profile definitions.

Supports:
- CSV files
- JSON files

Profiles define their own header signatures.
"""

from typing import Set

from src.ai.header_extraction_agent import HeaderExtractionAgent
from src.profiles.profile_registry import ProfileRegistry


class ProfileDetector:
    """
    Detect customer profiles from incoming files.
    """

    def __init__(self):
        self.registry = ProfileRegistry()
        self.header_extraction_agent = HeaderExtractionAgent()

    def detect_profile(
        self,
        file_path: str,
    ) -> str:
        headers = self._read_headers(file_path)
        profiles = self.registry.get_profiles()

        for profile_name, profile in profiles.items():
            signature = set(
                profile.get("header_signature", [])
            )

            if not signature:
                continue

            if signature.issubset(headers):
                return profile_name

        raise ValueError(
            f"No matching customer profile found for file: {file_path}"
        )

    def _read_headers(
        self,
        file_path: str,
    ) -> Set[str]:
        headers = self.header_extraction_agent.extract_headers(file_path)

        return {
            header.strip()
            for header in headers
        }