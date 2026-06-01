from tools.conversion_tools import (
    convert_csv_to_wms_xml,
    convert_json_to_wms_xml,
    convert_xml_to_wms_xml,
)

from tools.schema_detection_tools import (
    detect_schema,
    detect_csv_schema,
    detect_json_schema,
    detect_xml_schema,
)

from tools.mapping_tools import (
    generate_mapping_from_fields,
    save_mapping_config,
)

from tools.validation_tools import (
    validate_wms_xml_file,
)


TOOLS = {
    "convert_csv_to_wms_xml": convert_csv_to_wms_xml,
    "convert_json_to_wms_xml": convert_json_to_wms_xml,
    "convert_xml_to_wms_xml": convert_xml_to_wms_xml,
    "detect_schema": detect_schema,
    "detect_csv_schema": detect_csv_schema,
    "detect_json_schema": detect_json_schema,
    "detect_xml_schema": detect_xml_schema,
    "generate_mapping_from_fields": generate_mapping_from_fields,
    "save_mapping_config": save_mapping_config,
    "validate_wms_xml_file": validate_wms_xml_file,
}