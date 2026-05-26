from pathlib import Path
import xml.etree.ElementTree as ET


def parse_xml_file(file_path: str):
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    tree = ET.parse(path)
    root = tree.getroot()

    return root


def print_xml_structure(file_path: str):
    root = parse_xml_file(file_path)

    print(f"\nRoot: {root.tag}")

    for child in root:
        print(f"  Entity: {child.tag}")

        for field in child:
            if len(field) == 0:
                print(f"    Field: {field.tag} = {field.text}")
            else:
                print(f"    Nested Entity: {field.tag}")

                for nested_field in field:
                    print(
                        f"      Field: {nested_field.tag} = {nested_field.text}"
                    )


if __name__ == "__main__":

    print("ITEM IMPORT SAMPLE")
    print_xml_structure(
        "data/sample_files/CFG-IMP-ARTICOLI.xml"
    )

    print("\nORDER IMPORT SAMPLE")
    print_xml_structure(
        "data/sample_files/CFG-IMP-ORDINI.xml"
    )