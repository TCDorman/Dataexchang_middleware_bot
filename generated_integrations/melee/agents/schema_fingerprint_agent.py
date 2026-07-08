import json
import hashlib
from datetime import datetime
from pathlib import Path


# ==================================================
# Customer Name Normalization
# ==================================================
def get_safe_customer_name(customer_name: str):
    """
    Convert a customer name into a safe filename.

    Example:
    Ford Motor Company -> ford_motor_company
    """
    return customer_name.lower().replace(" ", "_")


# ==================================================
# Normalize Columns
# ==================================================
def normalize_columns(columns):
    """
    Normalize columns before creating a schema fingerprint.

    This prevents tiny formatting differences from creating
    unnecessary schema changes.

    Example:
    "PO NUM" -> "po_num"
    """
    return sorted(
        [
            str(column)
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
            .replace(".", "_")
            for column in columns
        ]
    )


# ==================================================
# Create Fingerprint
# ==================================================
def create_schema_fingerprint(columns):
    """
    Create a stable hash from a set of column names.

    Same columns = same fingerprint.
    Different columns = different fingerprint.
    """
    normalized_columns = normalize_columns(columns)

    fingerprint_source = "|".join(normalized_columns)

    fingerprint = hashlib.sha256(
        fingerprint_source.encode("utf-8")
    ).hexdigest()

    return {
        "fingerprint": fingerprint,
        "normalized_columns": normalized_columns,
    }


# ==================================================
# Schema Registry Path
# ==================================================
def get_schema_registry_path(customer_name: str):
    """
    Return the schema registry file path for a customer.
    """
    safe_name = get_safe_customer_name(customer_name)

    registry_dir = Path("configs/schema_fingerprints")
    registry_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return registry_dir / f"{safe_name}_schemas.json"


# ==================================================
# Load Schema Registry
# ==================================================
def load_schema_registry(customer_name: str):
    """
    Load known schema fingerprints for a customer.
    """
    registry_path = get_schema_registry_path(customer_name)

    if not registry_path.exists():
        return {
            "customer_name": customer_name,
            "schemas": [],
        }

    with open(
        registry_path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# ==================================================
# Save Schema Registry
# ==================================================
def save_schema_registry(customer_name: str, registry: dict):
    """
    Save known schema fingerprints for a customer.
    """
    registry_path = get_schema_registry_path(customer_name)

    with open(
        registry_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            registry,
            file,
            indent=4,
        )

    return str(registry_path)


# ==================================================
# Register Or Detect Schema
# ==================================================
def register_or_detect_schema_change(
    customer_name: str,
    file_path: str,
    columns,
):
    """
    Compare the current file schema against known schemas.

    Returns:
    - new_schema if this customer has never used this schema
    - known_schema if it has been seen before
    """
    registry = load_schema_registry(customer_name)

    fingerprint_data = create_schema_fingerprint(columns)

    current_fingerprint = fingerprint_data["fingerprint"]

    for schema in registry["schemas"]:
        if schema["fingerprint"] == current_fingerprint:
            return {
                "status": "known_schema",
                "registry_path": str(
                    get_schema_registry_path(customer_name)
                ),
                "schema": schema,
            }

    new_schema = {
        "fingerprint": current_fingerprint,
        "first_seen": datetime.now().isoformat(),
        "last_seen": datetime.now().isoformat(),
        "file_path": file_path,
        "columns": list(columns),
        "normalized_columns": fingerprint_data["normalized_columns"],
    }

    registry["schemas"].append(new_schema)

    registry_path = save_schema_registry(
        customer_name,
        registry,
    )

    return {
        "status": "new_schema",
        "registry_path": registry_path,
        "schema": new_schema,
    }