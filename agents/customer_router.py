import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.integration_agent import (
    process_csv_files,
    process_json_file,
)

from agents.customer_onboarding_agent import (
    create_customer_profile,
)

from agents.code_generation_agent import (
    generate_integration_package,
)

from agents.schema_intelligence_agent import (
    infer_mapping_with_samples,
)

from tools.tool_registry import TOOLS


# ==================================================
# Customer Profile Lookup
# ==================================================
def customer_profile_exists(customer_name: str):
    """
    Check whether a reusable customer profile already
    exists for this customer.

    Example:
    Ford -> configs/customers/ford_profile.json
    """
    safe_name = customer_name.lower().replace(" ", "_")

    profile_path = (
        Path("configs/customers")
        / f"{safe_name}_profile.json"
    )

    return profile_path.exists(), str(profile_path)


# ==================================================
# Source Type Detection
# ==================================================
def detect_source_type(file_paths: list[str]):
    """
    Determine the source file type based on file extensions.

    Current supported source types:
    - csv
    - json
    """
    extensions = [
        Path(file).suffix.lower()
        for file in file_paths
    ]

    if all(extension == ".csv" for extension in extensions):
        return "csv"

    if len(file_paths) == 1 and extensions[0] == ".json":
        return "json"

    return "unknown"


# ==================================================
# Extract Output Path
# ==================================================
def extract_output_path(result):
    """
    Try to find the generated output path from the conversion
    result returned by the integration pipeline.

    This is defensive because different tools may return
    slightly different result shapes.
    """
    if not isinstance(result, dict):
        return None

    if "output_path" in result:
        return result["output_path"]

    if "conversion" in result and isinstance(result["conversion"], dict):
        return result["conversion"].get("output_path")

    if "result" in result and isinstance(result["result"], dict):
        return extract_output_path(result["result"])

    return None


# ==================================================
# Build Mapping Snapshot
# ==================================================
def build_mapping_snapshot(file_paths: list[str], source_type: str):
    """
    Build a mapping snapshot for generated middleware packages.

    For CSV files, this uses the schema intelligence agent to
    infer field mappings from the customer's actual files.

    For non-CSV sources, this returns an empty mapping for now.
    """
    if source_type != "csv":
        return {}

    mapping_snapshot = {}

    for file_path in file_paths:
        analysis = infer_mapping_with_samples(file_path)

        mapping_snapshot[file_path] = {
            "columns": analysis["columns"],
            "mapping": analysis["mapping"],
            "confidence": analysis["confidence"],
            "sample_rows": analysis["sample_rows"],
        }

    return mapping_snapshot


# ==================================================
# Process Customer Files
# ==================================================
def process_customer_files(
    customer_name: str,
    file_paths: list[str],
):
    """
    Route customer files through the correct processing path.

    Workflow:
    1. Check if the customer already has a profile
    2. If yes, use the existing profile-based conversion tool
    3. If no, process as a new customer
    4. After successful new-customer processing, create a profile
    5. Generate a reusable middleware starter package
    """
    exists, profile_path = customer_profile_exists(
        customer_name
    )

    if exists:
        print(f"\nExisting customer found: {customer_name}")

        result = TOOLS["convert_existing_customer_files"](
            profile_path,
            file_paths,
        )

        return {
            "customer_exists": True,
            "profile_path": profile_path,
            "result": result,
        }

    print(
        f"\nNew customer detected: "
        f"{customer_name}"
    )

    if not file_paths:
        raise ValueError(
            "No input files were provided."
        )

    source_type = detect_source_type(file_paths)

    extensions = [
        Path(file).suffix.lower()
        for file in file_paths
    ]

    # ----------------------------------------------
    # Single CSV File
    # ----------------------------------------------
    if (
        len(file_paths) == 1
        and extensions[0] == ".csv"
    ):
        result = process_csv_files(
            file_paths[0],
            None,
            customer_name,
        )

    # ----------------------------------------------
    # Header + Line CSV Files
    # ----------------------------------------------
    elif (
        len(file_paths) == 2
        and all(ext == ".csv" for ext in extensions)
    ):
        result = process_csv_files(
            file_paths[0],
            file_paths[1],
            customer_name,
        )

    # ----------------------------------------------
    # Single JSON File
    # ----------------------------------------------
    elif (
        len(file_paths) == 1
        and extensions[0] == ".json"
    ):
        result = process_json_file(
            file_paths[0],
            customer_name,
        )

    else:
        raise ValueError(
            f"Unsupported input: {file_paths}"
        )

    output_path = extract_output_path(result)

    # ----------------------------------------------
    # Create Reusable Profile for New Customer
    # ----------------------------------------------
    profile_result = create_customer_profile(
        customer_name=customer_name,
        source_type=source_type,
        approved_mapping_path="configs\\mappings\\approved_agent_csv_mapping.json",
        output_format="wms_xml",
        output_path=output_path,
    )

    # ----------------------------------------------
    # Generate Integration Package for New Customer
    # ----------------------------------------------
    mapping_snapshot = build_mapping_snapshot(
        file_paths=file_paths,
        source_type=source_type,
    )

    package_result = generate_integration_package(
        customer_name=customer_name,
        source_type=source_type,
        mapping=mapping_snapshot,
    )

    return {
        "customer_exists": False,
        "profile_created": True,
        "profile_path": profile_result["profile_path"],
        "integration_package_created": True,
        "integration_package": package_result,
        "result": result,
    }


# ==================================================
# Manual Test
# ==================================================
if __name__ == "__main__":

    result = process_customer_files(
        "Ford",
        [
            "data/sample_files/test_ui_headers.csv",
            "data/sample_files/test_ui_lines.csv",
        ],
    )

    print("\nResult:")
    print(result)