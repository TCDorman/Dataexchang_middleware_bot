import pandas as pd

from tools.customer_profile_tools import (
    load_customer_profile,
    update_last_successful_run,
)

from tools.conversion_tools import (
    convert_csv_to_wms_xml,
    convert_json_to_wms_xml,
)

from tools.validation_tools import (
    validate_wms_xml_file,
)

from agents.schema_fingerprint_agent import (
    register_or_detect_schema_change,
)


# ==================================================
# Register CSV Schemas
# ==================================================
def register_csv_schemas(
    customer_name: str,
    file_paths: list[str],
):
    """
    Register schema fingerprints for successfully processed
    CSV files.

    This should only run after conversion + validation succeed.
    """
    schema_results = []

    for file_path in file_paths:
        df = pd.read_csv(file_path)

        schema_result = register_or_detect_schema_change(
            customer_name=customer_name,
            file_path=file_path,
            columns=df.columns,
        )

        schema_results.append(schema_result)

    return schema_results


# ==================================================
# Convert Existing Customer Files
# ==================================================
def convert_existing_customer_files(
    profile_path: str,
    file_paths: list[str],
):
    """
    Convert files for a customer that already has a profile.

    Supports:
    - CSV single-file orders
    - CSV header/line file pairs
    - JSON order files

    Also records schema fingerprints for successfully
    processed CSV files.
    """
    profile = load_customer_profile(profile_path)

    customer_name = profile["customer_name"]
    source_type = profile["source_type"]

    schema_results = []

    # ----------------------------------------------
    # Existing Customer CSV Conversion
    # ----------------------------------------------
    if source_type == "csv":

        if not file_paths:
            raise ValueError(
                "No CSV files were provided for conversion."
            )

        header_file_path = file_paths[0]

        # Single-file CSV support:
        # If only one CSV is provided, line_file_path stays None.
        line_file_path = (
            file_paths[1]
            if len(file_paths) > 1
            else None
        )

        conversion_result = convert_csv_to_wms_xml(
            header_file_path,
            line_file_path,
            "data/output/profile_csv_output.xml",
        )

    # ----------------------------------------------
    # Existing Customer JSON Conversion
    # ----------------------------------------------
    elif source_type == "json":

        if not file_paths:
            raise ValueError(
                "No JSON file was provided for conversion."
            )

        conversion_result = convert_json_to_wms_xml(
            file_paths[0],
            "data/output/profile_json_output.xml",
        )

    else:
        raise ValueError(
            f"Unsupported source type: {source_type}"
        )

    # ----------------------------------------------
    # Validate Generated XML
    # ----------------------------------------------
    validation_result = validate_wms_xml_file(
        conversion_result["output_path"]
    )

    # ----------------------------------------------
    # Register CSV Schema Fingerprints
    # ----------------------------------------------
    if source_type == "csv":
        schema_results = register_csv_schemas(
            customer_name=customer_name,
            file_paths=file_paths,
        )

    # ----------------------------------------------
    # Update Customer Profile Last Success
    # ----------------------------------------------
    update_last_successful_run(
        profile_path,
        conversion_result["output_path"],
    )

    return {
        "status": "success",
        "profile_path": profile_path,
        "source_type": source_type,
        "conversion": conversion_result,
        "validation": validation_result,
        "schema_fingerprints": schema_results,
    }