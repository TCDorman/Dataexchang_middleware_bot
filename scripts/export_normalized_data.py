import sys
from pathlib import Path
import json

sys.path.append(str(Path(__file__).resolve().parents[1]))

from parsers.xml_parser import parse_items, parse_orders


items = parse_items("data/sample_files/CFG-IMP-ARTICOLI.xml")
orders = parse_orders("data/sample_files/CFG-IMP-ORDINI.xml")

output = {
    "items": [item.model_dump() for item in items],
    "orders": [order.model_dump() for order in orders],
}

Path("data/processed").mkdir(parents=True, exist_ok=True)

with open("data/processed/normalized_output.json", "w") as f:
    json.dump(output, f, indent=4)

print("Normalized data exported to data/processed/normalized_output.json")