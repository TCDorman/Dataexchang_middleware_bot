import sys
from pathlib import Path
import json

sys.path.append(str(Path(__file__).resolve().parents[1]))

from parsers.rest_api_parser import parse_api_orders
from transformers.wms_xml_transformer import export_orders_to_xml


if __name__ == "__main__":

    if len(sys.argv) < 2:
        raise ValueError(
            "Usage: python scripts/convert_api_to_wms_xml.py <input_json_file>"
        )

    input_path = Path(sys.argv[1])

    if not input_path.exists():
        raise FileNotFoundError(f"Input JSON file not found: {input_path}")

    output_path = Path("data/output/api_orders_wms.xml")

    print(f"Reading API file: {input_path}")

    with open(input_path, "r") as file:
        api_data = json.load(file)

    Path("data/output").mkdir(parents=True, exist_ok=True)

    orders = parse_api_orders(api_data)

    print(f"Parsed {len(orders)} API orders")

    export_orders_to_xml(
        orders,
        output_path,
    )

    print(f"Generated {output_path}")