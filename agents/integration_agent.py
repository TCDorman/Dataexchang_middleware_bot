import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools.tool_registry import TOOLS


# ==================================================
# Process CSV Files
# ==================================================
def process_csv_files(
    header_file_path: str,
    line_file_path: str | None = None,
    customer_name: str = "Test CSV Customer",
):
    """
    Process customer CSV input files.

    Supports:
    - Single flat CSV file
    - Header CSV + line CSV file pair
    """
    print(
        f"\nProcessing CSV files:\n"
        f"Header: {header_file_path}\n"
        f"Lines: {line_file_path}"
    )

    # ----------------------------------------------
    # Detect header/single-file schema
    # ----------------------------------------------
    header_schema = TOOLS["detect_csv_schema"](
        header_file_path
    )

    # ----------------------------------------------
    # Detect line schema only if a line file exists
    # ----------------------------------------------
    if line_file_path:
        line_schema = TOOLS["detect_csv_schema"](
            line_file_path
        )

        all_fields = (
            header_schema["fields"]
            + line_schema["fields"]
        )

    else:
        line_schema = None
        all_fields = header_schema["fields"]

    print("\nDetected Fields:")
    for field in all_fields:
        print(f"  - {field}")

    # ----------------------------------------------
    # Generate mapping from detected fields
    # ----------------------------------------------
    mapping_result = TOOLS["generate_mapping_from_fields"](
        all_fields
    )

    mapping_path = "configs/mappings/agent_csv_mapping.json"

    TOOLS["save_mapping_config"](
        mapping_result,
        mapping_path,
    )

    # ----------------------------------------------
    # Save approved mapping
    # ----------------------------------------------
    approved_mapping_path = (
        "configs/mappings/approved_agent_csv_mapping.json"
    )

    approval_result = TOOLS["save_approved_mapping"](
        mapping_result,
        approved_mapping_path,
    )

    print(f"\nSaved Mapping:\n{mapping_path}")
    print(
        f"\nSaved Approved Mapping:\n"
        f"{approval_result['approved_mapping_path']}"
    )

    # ----------------------------------------------
    # Convert CSV to WMS XML
    # ----------------------------------------------
    conversion_result = TOOLS["convert_csv_to_wms_xml"](
        header_file_path,
        line_file_path,
        "data/output/agent_csv_output.xml",
    )

    print(f"\nConverted:\n{conversion_result['output_path']}")

    # ----------------------------------------------
    # Validate generated WMS XML
    # ----------------------------------------------
    validation_result = TOOLS["validate_wms_xml_file"](
        conversion_result["output_path"]
    )

    print("\nValidation:")
    print(validation_result)

    # ----------------------------------------------
    # Create/update customer profile
    # ----------------------------------------------
    profile_result = TOOLS["create_customer_profile"](
        customer_name=customer_name,
        source_type="csv",
        approved_mapping_path=approval_result[
            "approved_mapping_path"
        ],
    )

    TOOLS["update_last_successful_run"](
        profile_result["profile_path"],
        conversion_result["output_path"],
    )

    return {
        "header_schema": header_schema,
        "line_schema": line_schema,
        "mapping_file": mapping_path,
        "approved_mapping_file": approval_result[
            "approved_mapping_path"
        ],
        "conversion": conversion_result,
        "validation": validation_result,
        "customer_profile": profile_result,
    }


# ==================================================
# Process JSON File
# ==================================================
def process_json_file(
    file_path: str,
    customer_name: str = "Test JSON Customer",
):
    """
    Process a customer JSON input file and convert it
    into Modula WMS XML.
    """
    print(f"\nProcessing JSON file: {file_path}")

    # ----------------------------------------------
    # Detect JSON schema
    # ----------------------------------------------
    schema = TOOLS["detect_schema"](file_path)

    # ----------------------------------------------
    # Generate mapping from detected JSON fields
    # ----------------------------------------------
    mapping_result = TOOLS["generate_mapping_from_fields"](
        schema["fields"]
    )

    mapping_path = "configs/mappings/agent_json_mapping.json"

    TOOLS["save_mapping_config"](
        mapping_result,
        mapping_path,
    )

    # ----------------------------------------------
    # Save approved mapping
    # ----------------------------------------------
    approved_mapping_path = (
        "configs/mappings/approved_agent_json_mapping.json"
    )

    approval_result = TOOLS["save_approved_mapping"](
        mapping_result,
        approved_mapping_path,
    )

    # ----------------------------------------------
    # Convert JSON to WMS XML
    # ----------------------------------------------
    conversion_result = TOOLS["convert_json_to_wms_xml"](
        file_path,
        "data/output/agent_json_output.xml",
    )

    # ----------------------------------------------
    # Validate generated WMS XML
    # ----------------------------------------------
    validation_result = TOOLS["validate_wms_xml_file"](
        conversion_result["output_path"]
    )

    # ----------------------------------------------
    # Create/update customer profile
    # ----------------------------------------------
    profile_result = TOOLS["create_customer_profile"](
        customer_name=customer_name,
        source_type="json",
        approved_mapping_path=approval_result[
            "approved_mapping_path"
        ],
    )

    TOOLS["update_last_successful_run"](
        profile_result["profile_path"],
        conversion_result["output_path"],
    )

    return {
        "schema": schema,
        "mapping_file": mapping_path,
        "approved_mapping_file": approval_result[
            "approved_mapping_path"
        ],
        "conversion": conversion_result,
        "validation": validation_result,
        "customer_profile": profile_result,
    }


# ==================================================
# Manual Test
# ==================================================
if __name__ == "__main__":
    result = process_csv_files(
        "data/sample_files/test_ui_headers.csv",
        "data/sample_files/test_ui_lines.csv",
        customer_name="Test CSV Customer",
    )

    print("\nFinal Result:")
    print(result)