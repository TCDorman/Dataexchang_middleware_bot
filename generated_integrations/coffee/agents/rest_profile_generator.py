"""
rest_profile_generator.py

Generates and saves a customer profile from a confirmed
REST API field mapping.
"""

import json
from pathlib import Path


def save_rest_profile(
    customer_name: str,
    confirmed_mapping: dict,
) -> str:
    """
    Save a REST API mapping as a reusable customer profile.

    Returns:
        Path to the generated profile.
    """

    safe_name = (
        customer_name.strip()
        .lower()
        .replace(" ", "_")
    )

    output_dir = Path("configs/customers")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{safe_name}_rest_profile.json"

    profile = {
        "customer_name": customer_name,
        "source_type": "rest_api",
        "field_mapping": confirmed_mapping,
    }

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(profile, file, indent=4)

    return str(output_path)