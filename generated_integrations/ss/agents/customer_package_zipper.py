"""
customer_package_zipper.py

Creates a customer-ready ZIP package from a generated local integration folder.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict


def get_safe_customer_name(customer_name: str) -> str:
    return customer_name.strip().lower().replace(" ", "_")


def package_customer_local_app(
    customer_name: str,
    generated_integrations_folder: str = "generated_integrations",
    output_folder: str = "generated_packages",
) -> Dict:
    safe_customer_name = get_safe_customer_name(customer_name)

    source_folder = Path(generated_integrations_folder) / safe_customer_name

    if not source_folder.exists():
        return {
            "status": "error",
            "message": "Generated customer integration folder not found.",
            "source_folder": str(source_folder),
        }

    Path(output_folder).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_base_path = Path(output_folder) / f"{safe_customer_name}_local_agent_package_{timestamp}"

    zip_path = shutil.make_archive(
        base_name=str(zip_base_path),
        format="zip",
        root_dir=source_folder,
    )

    return {
        "status": "success",
        "customer_name": customer_name,
        "source_folder": str(source_folder),
        "package_path": zip_path,
    }