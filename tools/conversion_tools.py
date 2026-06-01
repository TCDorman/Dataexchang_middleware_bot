import sys
from pathlib import Path
from scripts.convert_xml_with_mapping import convert_xml_with_mapping

sys.path.append(str(Path(__file__).resolve().parents[1]))

from parsers.csv_parser import parse_erp_orders_csv
from parsers.rest_api_parser import parse_api_orders
from transformers.wms_xml_transformer import export_orders_to_xml
from scripts.format_wms_xml import format_wms_xml

import json


def convert_csv_to_wms_xml(header_file_path: str, line_file_path: str, output_path: str):
    orders = parse_erp_orders_csv(header_file_path, line_file_path)

    export_orders_to_xml(orders, output_path)
    format_wms_xml(output_path)

    return {
        "status": "success",
        "source_type": "csv",
        "orders_converted": len(orders),
        "output_path": output_path,
    }


def convert_json_to_wms_xml(input_json_file_path: str, output_path: str):
    with open(input_json_file_path, "r", encoding="utf-8") as file:
        api_data = json.load(file)

    orders = parse_api_orders(api_data)

    export_orders_to_xml(orders, output_path)
    format_wms_xml(output_path)

    return {
        "status": "success",
        "source_type": "json",
        "orders_converted": len(orders),
        "output_path": output_path,
    }

def convert_xml_to_wms_xml(
    input_xml_file_path: str,
    mapping_config_path: str,
):
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