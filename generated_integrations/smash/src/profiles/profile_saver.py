"""
profile_saver.py

Saves AI-generated customer profiles after human approval.

Profiles are stored as JSON files in:

    configs/customers/
"""

import json
import re
from pathlib import Path
from typing import Dict


class ProfileSaver:
    """
    Saves customer profile dictionaries to disk.
    """

    def __init__(
        self,
        profiles_directory: str = "configs/customers",
    ):
        """
        Initialize profile saver.

        Args:
            profiles_directory: Directory where profiles are stored.
        """

        self.profiles_directory = Path(profiles_directory)
        self.profiles_directory.mkdir(parents=True, exist_ok=True)

    def save_profile(
        self,
        profile_name: str,
        profile: Dict,
    ) -> Dict:
        """
        Save a customer profile as JSON.

        Args:
            profile_name: Name to use for the profile file.
            profile: Profile dictionary to save.

        Returns:
            Save result.
        """

        safe_name = self._sanitize_profile_name(profile_name)
        profile_path = self.profiles_directory / f"{safe_name}.json"

        profile_path.write_text(
            json.dumps(profile, indent=4),
            encoding="utf-8",
        )

        return {
            "status": "success",
            "profile_name": safe_name,
            "profile_path": str(profile_path),
        }

    def _sanitize_profile_name(self, profile_name: str) -> str:
        """
        Convert a profile name into a safe filename.

        Args:
            profile_name: Raw profile name.

        Returns:
            Safe lowercase filename without extension.
        """

        safe_name = profile_name.strip().lower()
        safe_name = re.sub(r"[^a-z0-9_\\-]+", "_", safe_name)
        safe_name = safe_name.strip("_")

        if not safe_name:
            raise ValueError("Profile name cannot be empty.")

        return safe_name