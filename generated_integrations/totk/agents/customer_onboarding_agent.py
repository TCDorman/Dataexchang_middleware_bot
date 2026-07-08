import json
from datetime import datetime
from pathlib import Path


# ==================================================
# Customer Name Normalization
# ==================================================
def get_safe_customer_name(customer_name: str):
    """
    Convert customer names into safe filenames.

    Example:
    Ford Motor Company -> ford_motor_company
    """
    return customer_name.lower().replace(" ", "_")


# ==================================================
# Customer Profile Path
# ==================================================
def get_customer_profile_path(customer_name: str):
    """
    Build the standard customer profile path.

    Example:
    Ford -> configs/customers/ford_profile.json
    """
    safe_name = get_safe_customer_name(customer_name)

    return (
        Path("configs/customers")
        / f"{safe_name}_profile.json"
    )


# ==================================================
# Create Customer Profile
# ==================================================
def create_customer_profile(
    customer_name: str,
    source_type: str,
    approved_mapping_path: str,
    output_format: str = "wms_xml",
    output_path: str | None = None,
):
    """
    Create a reusable customer profile after a successful
    first-time customer conversion.
    """
    profile_path = get_customer_profile_path(customer_name)

    profile_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    profile_data = {
        "customer_name": customer_name,
        "source_type": source_type,
        "approved_mapping_path": approved_mapping_path,
        "output_format": output_format,
        "created_at": datetime.now().isoformat(),
        "last_successful_run": {
            "timestamp": datetime.now().isoformat(),
            "output_path": output_path,
        },
    }

    with open(
        profile_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            profile_data,
            file,
            indent=4,
        )

    return {
        "status": "success",
        "profile_path": str(profile_path),
        "profile": profile_data,
    }


# ==================================================
# Check Customer Profile
# ==================================================
def customer_profile_exists(customer_name: str):
    """
    Check whether a reusable customer profile already exists.
    """
    profile_path = get_customer_profile_path(customer_name)

    return profile_path.exists()