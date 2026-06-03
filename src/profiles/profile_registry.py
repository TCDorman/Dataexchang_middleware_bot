"""
profile_registry.py

Automatically discovers and loads customer profiles.

This allows new customer profiles to be added simply by dropping
a JSON file into:

    configs/customers/

No code changes required.
"""

import json
from pathlib import Path
from typing import Dict


class ProfileRegistry:
    """
    Discovers and loads customer profiles.
    """

    def __init__(
        self,
        profiles_directory: str = "configs/customers",
    ):
        """
        Initialize registry.

        Args:
            profiles_directory:
                Directory containing customer profile JSON files.
        """

        self.profiles_directory = Path(
            profiles_directory
        )

    def get_profiles(self) -> Dict[str, Dict]:
        """
        Load all customer profiles.

        Returns:
            Dictionary of profiles keyed by profile name.

        Example:

        {
            "ford": {...},
            "acme": {...}
        }
        """

        profiles = {}

        if not self.profiles_directory.exists():
            return profiles

        for profile_file in self.profiles_directory.glob(
            "*.json"
        ):
            profile_name = profile_file.stem

            with open(
                profile_file,
                "r",
                encoding="utf-8",
            ) as file:

                profiles[profile_name] = json.load(
                    file
                )

        return profiles