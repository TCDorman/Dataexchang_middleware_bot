"""
Generated API Runner
Customer: demo_erp

Purpose:
    Fetches orders from the customer API and converts
    them into Modula WMS XML.
"""

# ==================================================
# Imports
# ==================================================

import json
from pathlib import Path

from api_client import GeneratedApiClient
from src.connectors.api_to_wms_pipeline import ApiToWmsPipeline


# ==================================================
# Helpers
# ==================================================

def load_config():
    """
    Load generated package config.
    """

    config_path = Path(__file__).parent / "config.json"

    with open(
        config_path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# ==================================================
# Main
# ==================================================

def main():
    """
    Run generated API integration.
    """

    config = load_config()

    client = GeneratedApiClient(
        config["api_config_path"]
    )

    api_response = client.fetch_orders(
        config["orders_endpoint"]
    )

    pipeline = ApiToWmsPipeline()

    result = pipeline.process_response(
        api_response=api_response,
        mapping_path=str(
            Path(__file__).parent / config["mapping_file"]
        ),
        output_path="data/output/demo_erp_api_orders.xml",
    )

    print("\nAPI INTEGRATION COMPLETE")
    print(result)


if __name__ == "__main__":
    main()
