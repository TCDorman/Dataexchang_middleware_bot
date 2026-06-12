import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from parsers.csv_parser import parse_erp_orders_csv
from transformers.wms_xml_transformer import export_orders_to_xml


if __name__ == "__main__":

    if len(sys.argv) < 3:
        raise ValueError(
            "Usage: python scripts/convert_erp_csv_to_wms_xml.py <header_csv_file> <line_csv_file>"
        )

    header_file_path = Path(sys.argv[1])
    line_file_path = Path(sys.argv[2])

    if not header_file_path.exists():
        raise FileNotFoundError(f"Header CSV file not found: {header_file_path}")

    if not line_file_path.exists():
        raise FileNotFoundError(f"Line CSV file not found: {line_file_path}")

    output_path = Path("data/output/customer_erp_orders_wms.xml")

    print(f"Reading header file: {header_file_path}")
    print(f"Reading line file: {line_file_path}")

    Path("data/output").mkdir(parents=True, exist_ok=True)

    orders = parse_erp_orders_csv(
        str(header_file_path),
        str(line_file_path),
    )

    print(f"Parsed {len(orders)} ERP orders")

    export_orders_to_xml(
        orders,
        output_path,
    )

    print(f"Generated {output_path}")