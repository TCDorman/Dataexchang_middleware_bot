import csv
import json
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from datetime import datetime
from typing import Any

from agents.openai_field_mapping_agent import infer_field_mapping_with_openai
from src.ai.header_extraction_agent import HeaderExtractionAgent
from src.converters.csv_to_canonical import CsvToCanonicalConverter
from src.formatters.modula_ordini_xml_formatter import ModulaOrdiniXmlFormatter


class FileProcessingPipeline:
    """
    Full pipeline:
    customer CSV / JSON / XML -> AI field mapping -> canonical orders
    -> Modula IMP_ORDINI XML.

    Important:
    CSV, JSON, and XML all use the same AI-driven mapping flow.
    The pipeline does NOT expect JSON/XML files to already use canonical fields.
    """

    def __init__(
        self,
        profiles_dir: str | Path,
        modula_output_dir: str | Path,
        processed_dir: str | Path,
        errors_dir: str | Path,
    ):
        self.profiles_dir = Path(profiles_dir)
        self.modula_output_dir = Path(modula_output_dir)
        self.processed_dir = Path(processed_dir)
        self.errors_dir = Path(errors_dir)

        self.header_agent = HeaderExtractionAgent()
        self.csv_converter = CsvToCanonicalConverter()
        self.formatter = ModulaOrdiniXmlFormatter()

        for d in [
            self.profiles_dir,
            self.modula_output_dir,
            self.processed_dir,
            self.errors_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)

    def _get_profile_path(self, customer_key: str) -> Path:
        return self.profiles_dir / f"{customer_key}_profile.json"

    def _load_profile(self, customer_key: str) -> dict | None:
        path = self._get_profile_path(customer_key)

        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

        return None

    def _save_profile(self, customer_key: str, profile: dict) -> None:
        path = self._get_profile_path(customer_key)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=4)

    def _customer_key(self, file_path: Path) -> str:
        return file_path.stem.lower().replace(" ", "_")

    def _output_xml_path(self, file_path: Path) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.modula_output_dir / f"IMP_ORDINI_{file_path.stem}_{timestamp}.xml"

    def _source_type(self, file_path: Path) -> str:
        extension = file_path.suffix.lower()

        if extension == ".csv":
            return "csv"

        if extension == ".json":
            return "json"

        if extension == ".xml":
            return "xml"

        raise ValueError(f"Unsupported input file type: {extension}")

    def _clean_value(self, value: Any) -> str:
        if value is None:
            return ""

        return str(value).strip()

    def _get_nested_value(self, source: dict, key: str, default: Any = "") -> Any:
        """
        Supports normal keys and dotted paths.

        Example:
            customer.name
            order.header.po_number
        """

        if not key:
            return default

        if key in source:
            return source.get(key, default)

        current = source

        for part in str(key).split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default

        return current

    def _flatten_dict(
        self,
        data: dict,
        parent_key: str = "",
        separator: str = ".",
    ) -> dict:
        """
        Flatten nested JSON dictionaries.

        Example:
            {"order": {"number": "PO1"}}
        becomes:
            {"order.number": "PO1"}
        """

        flattened = {}

        for key, value in data.items():
            new_key = f"{parent_key}{separator}{key}" if parent_key else str(key)

            if isinstance(value, dict):
                flattened.update(
                    self._flatten_dict(
                        value,
                        parent_key=new_key,
                        separator=separator,
                    )
                )
            elif isinstance(value, list):
                flattened[new_key] = value
            else:
                flattened[new_key] = value

        return flattened

    def _extract_csv_headers(self, file_path: Path) -> list[str]:
        return self.header_agent.extract_headers(str(file_path))

    def _extract_json_rows(self, file_path: Path) -> list[dict]:
        """
        Extract flat rows from customer JSON.

        Supports:
            [
                {"Purchase Order": "PO1", "Part Number": "BRG-100"}
            ]

        and:
            {
                "orders": [...]
            }
        """

        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, dict):
            if isinstance(data.get("orders"), list):
                records = data["orders"]
            elif isinstance(data.get("data"), list):
                records = data["data"]
            elif isinstance(data.get("items"), list):
                records = data["items"]
            else:
                records = [data]
        elif isinstance(data, list):
            records = data
        else:
            records = []

        rows = []

        for record in records:
            if not isinstance(record, dict):
                continue

            # If JSON already has nested lines, expand each line into a flat row.
            lines = record.get("lines")

            if isinstance(lines, list):
                header_data = {
                    key: value
                    for key, value in record.items()
                    if key != "lines"
                }

                for line in lines:
                    if not isinstance(line, dict):
                        continue

                    combined = {}
                    combined.update(self._flatten_dict(header_data))
                    combined.update(self._flatten_dict(line))
                    rows.append(combined)
            else:
                rows.append(self._flatten_dict(record))

        return rows

    def _extract_xml_rows(self, file_path: Path) -> list[dict]:
        """
        Extract flat row dictionaries from customer XML.

        This does not require canonical tags like order_id/item/quantity.
        It simply reads available XML tags so AI can map them.

        Example:
            <Order>
                <PurchaseOrder>PO1</PurchaseOrder>
                <PartNumber>BRG-100</PartNumber>
            </Order>

        becomes:
            {
                "PurchaseOrder": "PO1",
                "PartNumber": "BRG-100"
            }
        """

        tree = ET.parse(file_path)
        root = tree.getroot()
        rows = []

        for element in root.iter():
            children = list(element)

            if not children:
                continue

            row = {}

            for child in children:
                # Only treat simple children as fields.
                if list(child):
                    continue

                value = self._clean_value(child.text)

                if value:
                    row[child.tag] = value

            if row:
                rows.append(row)

        # Remove parent rows that do not contain enough useful fields.
        # For normal order XML, the useful rows are the repeated <Order> nodes.
        useful_rows = [
            row for row in rows
            if len(row.keys()) >= 2
        ]

        return useful_rows

    def _extract_source_fields(
        self,
        file_path: Path,
        source_type: str,
    ) -> list[str]:
        if source_type == "csv":
            return self._extract_csv_headers(file_path)

        if source_type == "json":
            rows = self._extract_json_rows(file_path)
            return self._collect_fields(rows)

        if source_type == "xml":
            rows = self._extract_xml_rows(file_path)
            return self._collect_fields(rows)

        raise ValueError(f"Unsupported source type: {source_type}")

    def _collect_fields(self, rows: list[dict]) -> list[str]:
        fields = []

        for row in rows:
            for field in row.keys():
                if field not in fields:
                    fields.append(field)

        return fields

    def _get_or_create_mapping_profile(
        self,
        file_path: Path,
        customer_key: str,
        source_type: str,
    ) -> dict:
        profile = self._load_profile(customer_key)

        if profile:
            print(f"[Pipeline] Loaded existing profile for '{customer_key}'")
            return profile

        source_fields = self._extract_source_fields(file_path, source_type)

        print(f"[Pipeline] Source fields found: {source_fields}")
        print("[Pipeline] No profile found — calling AI to infer mapping...")

        mapping_result = infer_field_mapping_with_openai(
            source_columns=source_fields,
            source_type=source_type,
        )

        field_mapping = mapping_result.get("field_mapping", {})

        profile = {
            "customer_key": customer_key,
            "source_type": source_type,
            "header_signature": source_fields,
            "field_mapping": field_mapping,
            "mapping_confidence": mapping_result.get("mapping_confidence", {}),
            "mapping_notes": mapping_result.get("mapping_notes", {}),
            "mapping_method": mapping_result.get("mapping_method"),
            "created_at": datetime.now().isoformat(),
        }

        self._save_profile(customer_key, profile)
        print(f"[Pipeline] Profile saved for '{customer_key}'")

        return profile

    def _rows_to_orders(
        self,
        rows: list[dict],
        field_mapping: dict,
    ) -> list[dict]:
        """
        Convert mapped flat rows into canonical grouped orders.

        field_mapping format:
            {
                "order_id": "PurchaseOrder",
                "customer_name": "Company",
                "item": "PartNumber",
                "quantity": "RequestedQty"
            }
        """

        grouped_orders = defaultdict(list)

        for row in rows:
            mapped_row = {}

            for internal_field, source_field in field_mapping.items():
                mapped_row[internal_field] = self._get_nested_value(
                    row,
                    source_field,
                    "",
                )

            order_id = self._clean_value(mapped_row.get("order_id"))
            item = self._clean_value(mapped_row.get("item"))

            if not order_id or not item:
                continue

            grouped_orders[order_id].append(mapped_row)

        orders = []

        for order_id, order_rows in grouped_orders.items():
            first_row = order_rows[0]

            order = {
                "order_id": order_id,
                "customer_name": self._clean_value(
                    first_row.get("customer_name")
                ),
                "lines": [],
            }

            for row in order_rows:
                quantity = self._clean_value(row.get("quantity"))

                order["lines"].append(
                    {
                        "item": self._clean_value(row.get("item")),
                        "quantity": quantity,
                    }
                )

            orders.append(order)

        return orders

    def _parse_csv(
        self,
        file_path: Path,
        customer_key: str,
        source_type: str,
    ) -> tuple[list[dict], str, dict]:
        profile = self._get_or_create_mapping_profile(
            file_path=file_path,
            customer_key=customer_key,
            source_type=source_type,
        )

        field_mapping = profile.get("field_mapping", {})
        print(f"[Pipeline] Field mapping: {field_mapping}")

        orders = self.csv_converter.convert(file_path, field_mapping)

        return orders, source_type, profile

    def _parse_json(
        self,
        file_path: Path,
        customer_key: str,
        source_type: str,
    ) -> tuple[list[dict], str, dict]:
        profile = self._get_or_create_mapping_profile(
            file_path=file_path,
            customer_key=customer_key,
            source_type=source_type,
        )

        field_mapping = profile.get("field_mapping", {})
        print(f"[Pipeline] Field mapping: {field_mapping}")

        rows = self._extract_json_rows(file_path)
        orders = self._rows_to_orders(rows, field_mapping)

        return orders, source_type, profile

    def _parse_xml(
        self,
        file_path: Path,
        customer_key: str,
        source_type: str,
    ) -> tuple[list[dict], str, dict]:
        profile = self._get_or_create_mapping_profile(
            file_path=file_path,
            customer_key=customer_key,
            source_type=source_type,
        )

        field_mapping = profile.get("field_mapping", {})
        print(f"[Pipeline] Field mapping: {field_mapping}")

        rows = self._extract_xml_rows(file_path)
        orders = self._rows_to_orders(rows, field_mapping)

        return orders, source_type, profile

    def _parse_input_file(
        self,
        file_path: Path,
        customer_key: str,
    ) -> tuple[list[dict], str, dict]:
        source_type = self._source_type(file_path)

        if source_type == "csv":
            return self._parse_csv(file_path, customer_key, source_type)

        if source_type == "json":
            return self._parse_json(file_path, customer_key, source_type)

        if source_type == "xml":
            return self._parse_xml(file_path, customer_key, source_type)

        raise ValueError(f"Unsupported source type: {source_type}")

    def process(self, file_path: str | Path) -> dict:
        file_path = Path(file_path)
        customer_key = self._customer_key(file_path)

        print(f"[Pipeline] Processing: {file_path.name}")

        try:
            orders, source_type, profile = self._parse_input_file(
                file_path=file_path,
                customer_key=customer_key,
            )

            print(f"[Pipeline] Source type: {source_type}")
            print(f"[Pipeline] Orders parsed: {len(orders)}")

            if not orders:
                raise ValueError(
                    "No valid orders found in file after AI/profile mapping."
                )

            output_path = self._output_xml_path(file_path)

            self.formatter.format_orders_to_xml(orders, output_path)

            print(f"[Pipeline] XML written: {output_path.name}")

            dest = self.processed_dir / file_path.name
            file_path.rename(dest)

            print(f"[Pipeline] Moved to processed: {dest.name}")

            return {
                "status": "success",
                "customer_key": customer_key,
                "source_type": source_type,
                "orders_processed": len(orders),
                "xml_output": str(output_path),
                "profile_used": str(self._get_profile_path(customer_key)),
                "field_mapping": profile.get("field_mapping", {}),
            }

        except Exception as e:
            dest = self.errors_dir / file_path.name

            if file_path.exists():
                file_path.rename(dest)

            print(f"[Pipeline] ERROR: {e} — moved to errors/")

            return {
                "status": "error",
                "file": str(file_path),
                "error": str(e),
            }