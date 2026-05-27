import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from parsers.csv_parser import parse_erp_orders_csv
from transformers.wms_xml_transformer import export_orders_to_xml


if __name__ == "__main__":
    print("Starting ERP CSV to WMS XML conversion...")

    Path("data/output").mkdir(parents=True, exist_ok=True)

    orders = parse_erp_orders_csv(
        "data/sample_files/customer_erp_order_headers.csv",
        "data/sample_files/customer_erp_order_lines.csv",
    )

    print(f"Parsed {len(orders)} orders")

    export_orders_to_xml(
        orders,
        "data/output/customer_erp_orders_wms.xml",
    )

    print("Converted ERP CSV files to data/output/customer_erp_orders_wms.xml")