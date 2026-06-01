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

from tools.approval_tools import (
    save_approved_mapping,
    load_approved_mapping,
)

from tools.validation_tools import (
    validate_wms_xml_file,
)

from tools.customer_profile_tools import (
    create_customer_profile,
    load_customer_profile,
    update_last_successful_run,
)

from tools.profile_conversion_tools import (
    convert_existing_customer_files,
)
from tools.export_tools import convert_wms_export_to_customer_csv

from tools.audit_tools import (
    write_audit_log,
    read_audit_log,
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
    "save_approved_mapping": save_approved_mapping,
    "load_approved_mapping": load_approved_mapping,
    "create_customer_profile": create_customer_profile,
    "load_customer_profile": load_customer_profile,
    "update_last_successful_run": update_last_successful_run,
    "convert_existing_customer_files": convert_existing_customer_files,
    "convert_wms_export_to_customer_csv": convert_wms_export_to_customer_csv,
    "write_audit_log": write_audit_log,
    "read_audit_log": read_audit_log,
}