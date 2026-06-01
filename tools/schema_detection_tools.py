import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd


def detect_csv_schema(file_path: str):
    df = pd.read_csv(file_path)

    return {
        "source_type": "csv",
        "file_path": file_path,
        "fields": list(df.columns),
        "sample_rows": df.head(3).to_dict(orient="records"),
    }


def collect_json_fields(data, prefix=""):
    fields = set()

    if isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            fields.add(full_key)
            fields.update(collect_json_fields(value, full_key))

    elif isinstance(data, list):
        for item in data:
            fields.update(collect_json_fields(item, prefix))

    return fields


def detect_json_schema(file_path: str):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return {
        "source_type": "json",
        "file_path": file_path,
        "fields": sorted(collect_json_fields(data)),
    }


def collect_xml_paths(element, prefix=""):
    fields = set()

    current_path = f"{prefix}.{element.tag}" if prefix else element.tag
    fields.add(current_path)

    for child in element:
        fields.update(collect_xml_paths(child, current_path))

    return fields


def detect_xml_schema(file_path: str):
    tree = ET.parse(file_path)
    root = tree.getroot()

    return {
        "source_type": "xml",
        "file_path": file_path,
        "fields": sorted(collect_xml_paths(root)),
    }


def detect_schema(file_path: str):
    extension = Path(file_path).suffix.lower()

    if extension == ".csv":
        return detect_csv_schema(file_path)

    if extension == ".json":
        return detect_json_schema(file_path)

    if extension == ".xml":
        return detect_xml_schema(file_path)

    raise ValueError(f"Unsupported file type: {extension}")