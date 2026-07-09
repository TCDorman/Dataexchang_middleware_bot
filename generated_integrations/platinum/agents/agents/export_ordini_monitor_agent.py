"""
export_ordini_monitor_agent.py

Watches for Modula/WMS export ordini files and automatically
converts them back into the customer's original file format.

After a WMS export file is processed, it is moved into a
processed folder so it is not exported repeatedly.
"""

import json
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from agents.agents.customer_order_export_agent import (
    export_orders_for_customer,
)


SUPPORTED_WMS_EXPORT_EXTENSIONS = {
    ".json",
}


def get_safe_customer_name(customer_name: str) -> str:
    return customer_name.strip().lower().replace(" ", "_")


def load_json_file(path: Path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_processed_wms_exports(state_path: str) -> Set[str]:
    path = Path(state_path)

    if not path.exists():
        return set()

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return set(data.get("processed_wms_exports", []))


def save_processed_wms_exports(
    state_path: str,
    processed_exports: Set[str],
) -> None:
    path = Path(state_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "processed_wms_exports": sorted(processed_exports),
        "updated_at": datetime.now().isoformat(),
    }

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def is_supported_wms_export_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_WMS_EXPORT_EXTENSIONS


def build_customer_output_path(
    output_folder: Path,
    customer_name: str,
    source_file: Path,
    output_extension: str = ".csv",
) -> Path:
    safe_customer_name = get_safe_customer_name(customer_name)

    output_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    return (
        output_folder
        / f"{safe_customer_name}_{source_file.stem}_customer_export{output_extension}"
    )


def build_processed_path(source_file: Path) -> Path:
    processed_folder = source_file.parent / "processed"
    processed_folder.mkdir(parents=True, exist_ok=True)

    processed_path = processed_folder / source_file.name

    if processed_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        processed_path = (
            processed_folder
            / f"{source_file.stem}_{timestamp}{source_file.suffix}"
        )

    return processed_path


def move_wms_export_to_processed(source_file: Path) -> Path:
    processed_path = build_processed_path(source_file)
    shutil.move(str(source_file), str(processed_path))
    return processed_path


def detect_customer_from_wms_export(
    wms_export_data,
    fallback_customer_name: Optional[str] = None,
) -> Optional[str]:
    if isinstance(wms_export_data, dict):
        possible_customer = (
            wms_export_data.get("customer_name")
            or wms_export_data.get("customer")
            or wms_export_data.get("company")
        )

        if possible_customer:
            return str(possible_customer)

        orders = wms_export_data.get("orders") or []

        if orders and isinstance(orders, list):
            first_order = orders[0]

            if isinstance(first_order, dict):
                possible_customer = (
                    first_order.get("customer_name")
                    or first_order.get("customer")
                    or first_order.get("company")
                )

                if possible_customer:
                    return str(possible_customer)

    return fallback_customer_name


def process_wms_export_file(
    wms_export_path: str,
    customer_name: Optional[str],
    output_folder: str = "data/customer_exports",
    move_processed_file: bool = True,
) -> Dict:
    source_file = Path(wms_export_path)

    if not source_file.exists():
        raise FileNotFoundError(f"WMS export file not found: {source_file}")

    if not is_supported_wms_export_file(source_file):
        return {
            "status": "skipped",
            "reason": "Unsupported WMS export file type.",
            "wms_export_path": str(source_file),
        }

    wms_export_data = load_json_file(source_file)

    detected_customer_name = detect_customer_from_wms_export(
        wms_export_data=wms_export_data,
        fallback_customer_name=customer_name,
    )

    if not detected_customer_name:
        return {
            "status": "skipped",
            "reason": "Could not determine customer for WMS export file.",
            "wms_export_path": str(source_file),
        }

    output_path = build_customer_output_path(
        output_folder=Path(output_folder),
        customer_name=detected_customer_name,
        source_file=source_file,
        output_extension=".csv",
    )

    result = export_orders_for_customer(
        customer_name=detected_customer_name,
        internal_orders_path=str(source_file),
        output_path=str(output_path),
    )

    result["automation"] = "export_ordini_monitor"
    result["wms_export_path"] = str(source_file)

    if move_processed_file and result.get("status") == "success":
        processed_path = move_wms_export_to_processed(source_file)
        result["processed_wms_export_path"] = str(processed_path)

    return result


def scan_wms_export_folder_once(
    watch_folder: str,
    customer_name: Optional[str] = None,
    output_folder: str = "data/customer_exports",
    already_processed: Optional[Set[str]] = None,
    move_processed_files: bool = True,
    processed_state_path: Optional[str] = None,
) -> List[Dict]:
    watch_path = Path(watch_folder)
    watch_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    if already_processed is None:
        already_processed = set()

    if processed_state_path:
        already_processed.update(
            load_processed_wms_exports(processed_state_path)
        )

    results = []

    for file_path in sorted(watch_path.iterdir()):
        resolved_path = str(file_path.resolve())

        if resolved_path in already_processed:
            continue

        if not is_supported_wms_export_file(file_path):
            continue

        result = process_wms_export_file(
            wms_export_path=str(file_path),
            customer_name=customer_name,
            output_folder=output_folder,
            move_processed_file=move_processed_files,
        )

        already_processed.add(resolved_path)
        results.append(result)

        if processed_state_path and result.get("status") == "success":
            save_processed_wms_exports(
                processed_state_path,
                already_processed,
            )

    return results


def watch_wms_export_folder(
    watch_folder: str,
    customer_name: Optional[str] = None,
    output_folder: str = "data/customer_exports",
    poll_seconds: int = 5,
    processed_state_path: Optional[str] = None,
):
    already_processed = set()

    while True:
        results = scan_wms_export_folder_once(
            watch_folder=watch_folder,
            customer_name=customer_name,
            output_folder=output_folder,
            already_processed=already_processed,
            move_processed_files=True,
            processed_state_path=processed_state_path,
        )

        for result in results:
            print(json.dumps(result, indent=4))

        time.sleep(poll_seconds)