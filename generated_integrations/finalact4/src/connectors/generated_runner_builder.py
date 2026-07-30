"""
==================================================
Generated Runner Builder
==================================================

Purpose:
    Generates executable runner.py files for generated
    REST API integration packages.

Responsibilities:
    - Load package config
    - Fetch orders from customer API
    - Process API response into WMS XML
"""

# ==================================================
# Imports
# ==================================================

from pathlib import Path
from typing import Dict


# ==================================================
# Generated Runner Builder
# ==================================================

class GeneratedRunnerBuilder:
    """
    Builds runnable integration runner files.
    """

    def build_runner(
        self,
        folder: Path,
        customer_name: str,
        analysis_result: Dict,
    ) -> str:
        """
        Generate executable runner.py.
        """

        runner_path = folder / "runner.py"

        output_path = (
            f"data/output/{customer_name}_api_orders.xml"
        )

        runner_path.write_text(
            f'''"""
Generated API Runner
Customer: {customer_name}

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
        output_path="{output_path}",
    )

    print("\\nAPI INTEGRATION COMPLETE")
    print(result)


if __name__ == "__main__":
    main()
''',
            encoding="utf-8",
        )

        return str(runner_path)