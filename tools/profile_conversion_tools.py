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


def convert_existing_customer_files(
    profile_path: str,
    file_paths: list[str],
):
    profile = load_customer_profile(profile_path)

    source_type = profile["source_type"]

    if source_type == "csv":
        conversion_result = convert_csv_to_wms_xml(
            file_paths[0],
            file_paths[1],
            "data/output/profile_csv_output.xml",
        )

    elif source_type == "json":
        conversion_result = convert_json_to_wms_xml(
            file_paths[0],
            "data/output/profile_json_output.xml",
        )

    else:
        raise ValueError(f"Unsupported source type: {source_type}")

    validation_result = validate_wms_xml_file(
        conversion_result["output_path"]
    )

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
    }