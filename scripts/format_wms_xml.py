import sys
from pathlib import Path
from xml.dom import minidom


def format_wms_xml(input_file_path: str, output_file_path: str | None = None):
    input_path = Path(input_file_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input XML file not found: {input_path}")

    if output_file_path:
        output_path = Path(output_file_path)
    else:
        output_path = input_path

    raw_xml = input_path.read_text(encoding="utf-8")

    parsed_xml = minidom.parseString(raw_xml)

    pretty_xml = parsed_xml.toprettyxml(indent="    ")

    # Remove extra blank lines created by minidom
    clean_xml = "\n".join(
        line for line in pretty_xml.splitlines() if line.strip()
    )

    output_path.write_text(clean_xml, encoding="utf-8")

    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError(
            "Usage: python scripts/format_wms_xml.py <input_xml_file> [output_xml_file]"
        )

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    formatted_path = format_wms_xml(input_file, output_file)

    print(f"Formatted WMS XML saved to: {formatted_path}")