import sys
from pathlib import Path
import json
import xml.etree.ElementTree as ET

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.mapping_agent import suggest_wms_mappings


def collect_xml_paths(element, prefix=""):
    fields = set()

    current_path = f"{prefix}.{element.tag}" if prefix else element.tag
    fields.add(current_path)

    for child in element:
        fields.update(collect_xml_paths(child, current_path))

    return fields


def generate_xml_mapping_config(input_xml_file, output_config_file):
    tree = ET.parse(input_xml_file)
    root = tree.getroot()

    fields = sorted(collect_xml_paths(root))

    result = suggest_wms_mappings(fields)

    config = {}

    for mapping in result.mappings:
        config[mapping.source_field] = {
            "internal_field": mapping.internal_field,
            "wms_field": mapping.suggested_wms_field,
            "confidence": mapping.confidence,
            "reason": mapping.reason,
        }

    output_path = Path(output_config_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=4)

    print(f"Generated XML mapping config: {output_path}")


if __name__ == "__main__":
    generate_xml_mapping_config(
        "data/sample_files/CFG-IMP-ORDINI.xml",
        "configs/mappings/xml_mapping_config.json",
    )