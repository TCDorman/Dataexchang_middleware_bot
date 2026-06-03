"""
profile_loader.py

Loads customer mapping profiles.

Profiles define how customer-specific fields map
to the internal Modula order format.
"""

import json
from pathlib import Path
from typing import Dict


class ProfileLoader:
    """
    Loads customer profile JSON files.
    """

    def __init__(
        self,
        profiles_directory: str = "configs/customers",
    ):
        self.profiles_directory = Path(profiles_directory)

    def load_profile(
        self,
        profile_name: str,
    ) -> Dict:
        """
        Load a customer profile.

        Args:
            profile_name: Name of the profile file.

        Returns:
            Profile dictionary.
        """

        profile_path = (
            self.profiles_directory
            / f"{profile_name}.json"
        )

        with open(profile_path, "r", encoding="utf-8") as file:
            return json.load(file)