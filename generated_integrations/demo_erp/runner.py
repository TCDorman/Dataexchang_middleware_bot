"""
Generated API Runner

Purpose:
    Runs the generated customer API integration.
"""

# ==================================================
# Imports
# ==================================================

import json
from pathlib import Path

from api_client import GeneratedApiClient


# ==================================================
# Helpers
# ==================================================

def load_config():
    """
    Load package config.json.
    """

    config_path = Path(__file__).parent / "config.json"

    with open(
        config_path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# ==================================================
# Main Runner
# ==================================================

def main():
    """
    Fetch orders from customer API.
    """

    config = load_config()

    client = GeneratedApiClient(
        config["api_config_path"]
    )

    orders_response = client.fetch_orders(
        config["orders_endpoint"]
    )

    print("API RESPONSE")
    print(json.dumps(orders_response, indent=4))


if __name__ == "__main__":
    main()
