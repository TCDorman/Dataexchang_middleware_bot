import json
from pathlib import Path
from datetime import datetime


CUSTOMER_PROFILE_DIR = Path("configs/customers")


def create_customer_profile(
    customer_name: str,
    source_type: str,
    approved_mapping_path: str,
    output_format: str = "wms_xml",
):
    CUSTOMER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    safe_name = customer_name.lower().replace(" ", "_")

    profile_path = CUSTOMER_PROFILE_DIR / f"{safe_name}_profile.json"

    profile = {
        "customer_name": customer_name,
        "source_type": source_type,
        "approved_mapping_path": approved_mapping_path,
        "output_format": output_format,
        "created_at": datetime.utcnow().isoformat(),
        "last_successful_run": None,
    }

    with open(profile_path, "w", encoding="utf-8") as file:
        json.dump(profile, file, indent=4)

    return {
        "status": "success",
        "profile_path": str(profile_path),
        "profile": profile,
    }


def load_customer_profile(profile_path: str):
    with open(profile_path, "r", encoding="utf-8") as file:
        return json.load(file)


def update_last_successful_run(profile_path: str, output_path: str):
    profile = load_customer_profile(profile_path)

    profile["last_successful_run"] = {
        "timestamp": datetime.utcnow().isoformat(),
        "output_path": output_path,
    }

    with open(profile_path, "w", encoding="utf-8") as file:
        json.dump(profile, file, indent=4)

    return {
        "status": "success",
        "profile_path": profile_path,
        "profile": profile,
    }