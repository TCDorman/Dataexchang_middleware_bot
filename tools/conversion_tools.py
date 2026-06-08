"""
==================================================
Conversion Tools
==================================================

Purpose:
    Converts customer source data into Modula WMS XML.

Responsibilities:
    - Convert CSV orders to WMS XML
    - Convert JSON orders to WMS XML
    - Convert XML orders using mapping logic
    - Run centralized order validation before export
"""

# ==================================================
# Imports
# ==================================================

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from parsers.csv_parser import parse_erp_orders_csv
from parsers.rest_api_parser import parse_api_orders
from scripts.convert_xml_with_mapping import convert_xml_with_mapping
from scripts.format_wms_xml import format_wms_xml
from src.validation.validation_manager import ValidationManager
from transformers.wms_xml_transformer import export_orders_to_xml


# ==================================================
# Order Validation
# ==================================================

def run_order_validation(orders: list):
    """
    Run centralized order validation before exporting.

    Args:
        orders:
            Normalized order list.

    Returns:
        Validation result.

    Raises:
        ValueError:
            If validation fails.
    """

    validation_manager = ValidationManager()

    validation_result = validation_manager.validate_orders(orders)

    if not validation_result["is_valid"]:
        raise ValueError(
            "Order validation failed: "
            f"{validation_result['errors']}"
        )

    return validation_result


# ==================================================
# Convert CSV to WMS XML
# ==================================================

def convert_csv_to_wms_xml(
    header_file_path: str,
    line_file_path: str | None,
    output_path: str,
):
    """
    Convert customer CSV order data into Modula WMS XML.

    Workflow:
    1. Parse CSV orders
    2. Run centralized order validation
    3. Export orders to XML
    4. Format XML output
    """

    orders = parse_erp_orders_csv(
        header_file_path,
        line_file_path,
    )

    validation_result = run_order_validation(orders)

    export_orders_to_xml(orders, output_path)
    format_wms_xml(output_path)

    return {
        "status": "success",
        "source_type": "csv",
        "orders_converted": len(orders),
        "validation_result": validation_result,
        "duplicate_check": validation_result["details"][
            "duplicate_check"
        ],
        "business_rule_check": validation_result["details"][
            "business_rule_check"
        ],
        "output_path": output_path,
    }


# ==================================================
# Convert JSON to WMS XML
# ==================================================

def convert_json_to_wms_xml(
    input_json_file_path: str,
    output_path: str,
):
    """
    Convert customer JSON order data into Modula WMS XML.

    Workflow:
    1. Load JSON file
    2. Parse JSON into normalized orders
    3. Run centralized order validation
    4. Export orders to XML
    5. Format XML output
    """

    with open(
        input_json_file_path,
        "r",
        encoding="utf-8",
    ) as file:
        api_data = json.load(file)

    orders = parse_api_orders(api_data)

    validation_result = run_order_validation(orders)

    export_orders_to_xml(orders, output_path)
    format_wms_xml(output_path)

    return {
        "status": "success",
        "source_type": "json",
        "orders_converted": len(orders),
        "validation_result": validation_result,
        "duplicate_check": validation_result["details"][
            "duplicate_check"
        ],
        "business_rule_check": validation_result["details"][
            "business_rule_check"
        ],
        "output_path": output_path,
    }


# ==================================================
# Convert XML to WMS XML
# ==================================================

def convert_xml_to_wms_xml(
    input_xml_file_path: str,
    mapping_config_path: str,
):
    """
    Convert customer XML order data into Modula WMS XML.

    Note:
        Central order validation is not currently applied here
        because this function delegates conversion to an XML
        mapping script.
    """

    output_path = "data/output/tool_xml_orders.xml"

    convert_xml_with_mapping(
        input_xml_file_path,
        mapping_config_path,
    )

    return {
        "status": "success",
        "source_type": "xml",
        "output_path": output_path,
    }