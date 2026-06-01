import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools.tool_registry import TOOLS

def process_csv_files(
    header_file_path: str,
    line_file_path: str,
):
    print(
        f"\nProcessing CSV files:\n"
        f"Header: {header_file_path}\n"
        f"Lines: {line_file_path}"
    )

    # Detect schemas
    header_schema = TOOLS["detect_csv_schema"](
        header_file_path
    )

    line_schema = TOOLS["detect_csv_schema"](
        line_file_path
    )

    all_fields = (
        header_schema["fields"]
        + line_schema["fields"]
    )

    print("\nDetected Fields:")

    for field in all_fields:
        print(f"  - {field}")

    # Generate mapping
    mapping_result = TOOLS[
        "generate_mapping_from_fields"
    ](all_fields)

    # Save mapping
    mapping_path = (
        "configs/mappings/"
        "agent_csv_mapping.json"
    )

    TOOLS["save_mapping_config"](
        mapping_result,
        mapping_path,
    )

    print(
        f"\nSaved Mapping:\n"
        f"{mapping_path}"
    )

    # Convert
    conversion_result = TOOLS[
        "convert_csv_to_wms_xml"
    ](
        header_file_path,
        line_file_path,
        "data/output/agent_csv_output.xml",
    )

    print(
        f"\nConverted:\n"
        f"{conversion_result['output_path']}"
    )

    # Validate
    validation_result = TOOLS[
        "validate_wms_xml_file"
    ](
        conversion_result["output_path"]
    )

    print(
        "\nValidation:"
    )

    print(validation_result)

    return {
        "header_schema": header_schema,
        "line_schema": line_schema,
        "mapping_file": mapping_path,
        "conversion": conversion_result,
        "validation": validation_result,
    }
def process_json_file(file_path: str):
    print(f"\nProcessing JSON file: {file_path}")

    schema = TOOLS["detect_schema"](file_path)

    mapping_result = TOOLS["generate_mapping_from_fields"](
        schema["fields"]
    )

    mapping_path = "configs/mappings/agent_json_mapping.json"

    TOOLS["save_mapping_config"](
        mapping_result,
        mapping_path,
    )

    conversion_result = TOOLS["convert_json_to_wms_xml"](
        file_path,
        "data/output/agent_json_output.xml",
    )

    validation_result = TOOLS["validate_wms_xml_file"](
        conversion_result["output_path"]
    )

    return {
        "schema": schema,
        "mapping_file": mapping_path,
        "conversion": conversion_result,
        "validation": validation_result,
    }
if __name__ == "__main__":
    result = process_csv_files(
        "data/sample_files/test_ui_headers.csv",
        "data/sample_files/test_ui_lines.csv",
    )

    print("\nFinal Result:")
    print(result)
    