import sys
from pathlib import Path
from scripts.convert_xml_with_mapping import convert_xml_with_mapping

sys.path.append(str(Path(__file__).resolve().parents[1]))

from parsers.csv_parser import parse_erp_orders_csv
from parsers.rest_api_parser import parse_api_orders
from transformers.wms_xml_transformer import export_orders_to_xml
from scripts.format_wms_xml import format_wms_xml
from src.validation.duplicate_detector import DuplicateDetector

import json


# ==================================================
# Duplicate Validation
# ==================================================

def run_duplicate_check(orders: list):
    """
    Run duplicate detection before exporting orders.

    Args:
        orders:
            Normalized order list.

    Returns:
        Duplicate detection result.

    Raises:
        ValueError:
            If duplicate order IDs are detected.
    """

    detector = DuplicateDetector()

    duplicate_result = detector.detect_duplicates(orders)

    if duplicate_result["duplicate_order_ids"]:
        raise ValueError(
            "Duplicate order IDs detected: "
            f"{duplicate_result['duplicate_order_ids']}"
        )

    return duplicate_result


# ==================================================
# Convert CSV to WMS XML
# ==================================================

def convert_csv_to_wms_xml(
    header_file_path: str,
    line_file_path: str,
    output_path: str,
):
    """
    Convert customer CSV order data into Modula WMS XML.

    Workflow:
    1. Parse CSV orders
    2. Detect duplicate orders/order lines
    3. Export orders to XML
    4. Format XML output
    """

    orders = parse_erp_orders_csv(
        header_file_path,
        line_file_path,
    )

    duplicate_result = run_duplicate_check(orders)

    export_orders_to_xml(orders, output_path)
    format_wms_xml(output_path)

    return {
        "status": "success",
        "source_type": "csv",
        "orders_converted": len(orders),
        "duplicate_check": duplicate_result,
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
    3. Detect duplicate orders/order lines
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

    duplicate_result = run_duplicate_check(orders)

    export_orders_to_xml(orders, output_path)
    format_wms_xml(output_path)

    return {
        "status": "success",
        "source_type": "json",
        "orders_converted": len(orders),
        "duplicate_check": duplicate_result,
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
        Duplicate detection is not currently applied here
        because this function delegates conversion to an
        XML mapping script.
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