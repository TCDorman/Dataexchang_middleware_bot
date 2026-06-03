"""
profile_detector.py

Detects customer profiles dynamically using profile definitions.

Profiles define their own header signatures.

This means new customers can be added simply by creating a
new JSON profile file in:

    configs/customers/
"""

import csv
from typing import Set

from src.profiles.profile_registry import ProfileRegistry


class ProfileDetector:
    """
    Detect customer profiles from incoming files.
    """

    def __init__(self):
        """
        Initialize detector.
        """

        self.registry = ProfileRegistry()

    def detect_profile(
        self,
        file_path: str,
    ) -> str:
        """
        Detect which customer profile matches the file.

        Args:
            file_path: Customer file path.

        Returns:
            Matching profile name.

        Raises:
            ValueError: If no matching profile is found.
        """

        headers = self._read_headers(file_path)
        profiles = self.registry.get_profiles()

        for profile_name, profile in profiles.items():
            signature = set(
                profile.get("header_signature", [])
            )

            # IMPORTANT:
            # Skip profiles that do not define a header signature.
            #
            # Without this check, an empty set would match every file
            # because set([]).issubset(headers) is always True.
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
        """
        Read CSV headers from a file.

        Args:
            file_path: CSV file path.

        Returns:
            Set of stripped header names.
        """

        with open(
            file_path,
            mode="r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.reader(file)
            headers = next(reader)

        return {
            header.strip()
            for header in headers
        }