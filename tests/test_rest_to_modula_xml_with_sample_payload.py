# tests/test_rest_to_modula_xml_with_sample_payload.py

import json
from pathlib import Path

from agents.rest_to_modula_xml_agent import (
    _ensure_list,
    _map_record,
    _write_modula_imp_ordini_xml,
)


with open("data/sample_files/rest_order_test.json", "r", encoding="utf-8") as file:
    payload = json.load(file)

with open("configs/customers/rest_order_test_profile.json", "r", encoding="utf-8") as file:
    profile = json.load(file)

records = _ensure_list(payload)

mapped_records = [
    _map_record(record, profile["field_mapping"])
    for record in records
]

output_path = _write_modula_imp_ordini_xml(
    records=mapped_records,
    output_folder="data/output",
)

print("REST SAMPLE PAYLOAD TO MODULA XML TEST")
print("=" * 60)
print(output_path)