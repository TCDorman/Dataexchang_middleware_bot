"""
rest_to_modula_xml_agent.py

Pulls live REST API data, applies a saved REST profile mapping,
deduplicates already-processed records, and exports the result into
Modula IMP_ORDINI XML.
"""

import json
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

from agents.rest_api_data_fetcher import fetch_rest_api_records


def _load_profile(profile_path: str) -> dict:
    with open(profile_path, "r", encoding="utf-8") as file:
        return json.load(file)


def _load_processed_record_ids(state_path: str) -> set:
    path = Path(state_path)

    if not path.exists():
        return set()

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return set(data.get("processed_record_ids", []))


def _save_processed_record_ids(state_path: str, processed_ids: set) -> None:
    path = Path(state_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "processed_record_ids": sorted(processed_ids),
        "updated_at": datetime.now().isoformat(),
    }

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def _get_value(record: dict, field_path: str):
    if not field_path:
        return None

    current = record

    for part in field_path.split("."):
        if not isinstance(current, dict):
            return None

        current = current.get(part)

    return current


def _get_record_id(record: dict) -> str:
    return str(
        record.get("order_id")
        or record.get("ORD_ORDINE")
        or record.get("id")
        or ""
    )


def _map_record(record: dict, field_mapping: dict) -> dict:
    mapped = {}

    for modula_field, source_field in field_mapping.items():
        if modula_field == "lines":
            continue

        mapped[modula_field] = _get_value(record, source_field)

    lines_config = field_mapping.get("lines")

    if isinstance(lines_config, dict):
        lines_path = lines_config.get("path", "lines")
        source_lines = _get_value(record, lines_path) or []

        mapped["lines"] = [
            {
                "item": _get_value(source_line, lines_config.get("item")),
                "quantity": _get_value(source_line, lines_config.get("quantity")),
            }
            for source_line in source_lines
        ]

    return mapped


def _add_text(parent, tag: str, value=None):
    element = ET.SubElement(parent, tag)

    if value is not None:
        element.text = str(value)

    return element


def _add_imp_ordini_line(order, order_id: str, item, quantity):
    line = ET.SubElement(order, "IMP_ORDINI_RIGHE")

    _add_text(line, "RIG_ORDINE", order_id)
    _add_text(line, "RIG_ARTICOLO", item)
    _add_text(line, "RIG_SUB1")
    _add_text(line, "RIG_SUB2")
    _add_text(line, "RIG_STAMATE")
    _add_text(line, "RIG_TIPOCONF")
    _add_text(line, "RIG_HOSTINF")
    _add_text(line, "RIG_QTAR", quantity)
    _add_text(line, "RIG_REQ_NOTE")
    _add_text(line, "RIG_NOTE_STAMPA")
    _add_text(line, "RIG_HOSTCAUS")
    _add_text(line, "RIG_HOSTRIF")


def _write_modula_imp_ordini_xml(
    records: list[dict],
    output_folder: str = "data/output",
) -> str:
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_folder) / f"rest_imp_ordini_{timestamp}.xml"

    root = ET.Element("SYSTORE")

    for record in records:
        order_id = record.get("order_id") or record.get("ORD_ORDINE") or ""
        description = record.get("description") or record.get("ORD_DES") or order_id
        operation_type = record.get("operation_type") or record.get("ORD_TIPOOP") or "P"

        order = ET.SubElement(root, "IMP_ORDINI")

        _add_text(order, "ORD_ORDINE", order_id)
        _add_text(order, "ORD_DES", description)
        _add_text(order, "ORD_TIPOOP", operation_type)

        lines = record.get("lines")

        if lines:
            for line in lines:
                _add_imp_ordini_line(
                    order=order,
                    order_id=order_id,
                    item=line.get("item"),
                    quantity=line.get("quantity"),
                )
        else:
            item = record.get("item") or record.get("RIG_ARTICOLO") or ""
            quantity = record.get("quantity") or record.get("RIG_QTAR") or 0

            _add_imp_ordini_line(
                order=order,
                order_id=order_id,
                item=item,
                quantity=quantity,
            )

    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

    return str(output_path)


def generate_modula_xml_from_rest_api(
    base_url: str,
    endpoint: str,
    profile_path: str,
    output_folder: str = "data/output",
    auth_type: str = "none",
    api_key: str | None = None,
    api_key_header: str = "Authorization",
    bearer_token: str | None = None,
    username: str | None = None,
    password: str | None = None,
    pagination_strategy: str = "none",
    results_key: str | None = None,
    max_pages: int = 10,
    processed_state_path: str = "generated_integrations/processed_rest_records.json",
) -> dict:
    profile = _load_profile(profile_path)
    field_mapping = profile.get("field_mapping", {})

    processed_ids = _load_processed_record_ids(processed_state_path)

    fetch_result = fetch_rest_api_records(
        base_url=base_url,
        endpoint=endpoint,
        auth_type=auth_type,
        api_key=api_key,
        api_key_header=api_key_header,
        bearer_token=bearer_token,
        username=username,
        password=password,
        pagination_strategy=pagination_strategy,
        results_key=results_key,
        max_pages=max_pages,
    )

    if fetch_result.get("status") != "success":
        return {
            "status": "error",
            "source_type": "rest_api",
            "message": "REST API data fetch failed.",
            "fetch_result": fetch_result,
        }

    records = fetch_result.get("records", [])

    new_records = []

    for record in records:
        record_id = _get_record_id(record)

        if not record_id:
            continue

        if record_id in processed_ids:
            continue

        new_records.append(record)

    if not new_records:
        return {
            "status": "skipped",
            "source_type": "rest_api",
            "message": "No new REST records to convert.",
            "records_fetched": len(records),
            "records_converted": 0,
            "duplicates_skipped": len(records),
            "processed_state_path": processed_state_path,
        }

    mapped_records = [
        _map_record(record, field_mapping)
        for record in new_records
    ]

    output_path = _write_modula_imp_ordini_xml(
        records=mapped_records,
        output_folder=output_folder,
    )

    for record in new_records:
        processed_ids.add(_get_record_id(record))

    _save_processed_record_ids(processed_state_path, processed_ids)

    return {
        "status": "success",
        "source_type": "rest_api",
        "document_type": "ordini",
        "xml_format": "IMP_ORDINI",
        "auth_type": auth_type,
        "pagination_strategy": pagination_strategy,
        "results_key": results_key,
        "max_pages": max_pages,
        "records_fetched": len(records),
        "new_records": len(new_records),
        "records_converted": len(mapped_records),
        "duplicates_skipped": len(records) - len(new_records),
        "output_path": output_path,
        "processed_state_path": processed_state_path,
    }