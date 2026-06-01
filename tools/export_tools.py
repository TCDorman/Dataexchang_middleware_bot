import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from parsers.wms_export_parser import parse_wms_order_export
from exporters.customer_csv_exporter import export_wms_orders_to_customer_csv


def convert_wms_export_to_customer_csv(
    wms_export_xml_path: str,
    output_csv_path: str,
):
    orders = parse_wms_order_export(wms_export_xml_path)

    output_file = export_wms_orders_to_customer_csv(
        orders,
        output_csv_path,
    )

    return {
        "status": "success",
        "source_type": "wms_export_xml",
        "target_type": "customer_csv",
        "orders_exported": len(orders),
        "output_path": str(output_file),
    }