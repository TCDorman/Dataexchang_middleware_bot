import json
from pathlib import Path
from datetime import datetime

from agents.openai_field_mapping_agent import infer_field_mapping_with_openai
from src.ai.header_extraction_agent import HeaderExtractionAgent
from src.converters.csv_to_canonical import CsvToCanonicalConverter
from src.formatters.modula_ordini_xml_formatter import ModulaOrdiniXmlFormatter

from src.parsing.json_order_parser import JsonOrderParser
from src.parsing.xml_order_parser import XmlOrderParser


class FileProcessingPipeline:
    """
    Full pipeline:
    customer CSV / JSON / XML -> canonical orders -> Modula IMP_ORDINI XML.
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
        self.converter = CsvToCanonicalConverter()
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
        stem = file_path.stem
        return self.modula_output_dir / f"IMP_ORDINI_{stem}_{timestamp}.xml"

    def _source_type(self, file_path: Path) -> str:
        extension = file_path.suffix.lower()

        if extension == ".csv":
            return "csv"

        if extension == ".json":
            return "json"

        if extension == ".xml":
            return "xml"

        raise ValueError(f"Unsupported input file type: {extension}")

    def _parse_csv(self, file_path: Path, customer_key: str) -> tuple[list[dict], str]:
        """
        CSV still uses AI header extraction and saved field mapping profiles.
        """

        headers = self.header_agent.extract_headers(str(file_path))
        print(f"[Pipeline] Headers found: {headers}")

        profile = self._load_profile(customer_key)

        if profile:
            print(f"[Pipeline] Loaded existing profile for '{customer_key}'")
            field_mapping = profile.get("field_mapping", {})
        else:
            print("[Pipeline] No profile found — calling AI to infer mapping...")

            mapping_result = infer_field_mapping_with_openai(
                source_columns=headers,
                source_type="csv",
            )

            field_mapping = mapping_result.get("field_mapping", {})

            profile = {
                "customer_key": customer_key,
                "source_type": "csv",
                "header_signature": headers,
                "field_mapping": field_mapping,
                "mapping_confidence": mapping_result.get("mapping_confidence", {}),
                "mapping_notes": mapping_result.get("mapping_notes", {}),
                "mapping_method": mapping_result.get("mapping_method"),
                "created_at": datetime.now().isoformat(),
            }

            self._save_profile(customer_key, profile)
            print(f"[Pipeline] Profile saved for '{customer_key}'")

        print(f"[Pipeline] Field mapping: {field_mapping}")

        orders = self.converter.convert(file_path, field_mapping)
        return orders, "csv"

    def _parse_json(self, file_path: Path) -> tuple[list[dict], str]:
        parser = JsonOrderParser()
        orders = parser.parse(str(file_path))
        return orders, "json"

    def _parse_xml(self, file_path: Path) -> tuple[list[dict], str]:
        parser = XmlOrderParser()
        orders = parser.parse(str(file_path))
        return orders, "xml"

    def _parse_input_file(self, file_path: Path, customer_key: str) -> tuple[list[dict], str]:
        source_type = self._source_type(file_path)

        if source_type == "csv":
            return self._parse_csv(file_path, customer_key)

        if source_type == "json":
            return self._parse_json(file_path)

        if source_type == "xml":
            return self._parse_xml(file_path)

        raise ValueError(f"Unsupported source type: {source_type}")

    def process(self, file_path: str | Path) -> dict:
        file_path = Path(file_path)
        customer_key = self._customer_key(file_path)

        print(f"[Pipeline] Processing: {file_path.name}")

        try:
            orders, source_type = self._parse_input_file(file_path, customer_key)

            print(f"[Pipeline] Source type: {source_type}")
            print(f"[Pipeline] Orders parsed: {len(orders)}")

            if not orders:
                raise ValueError("No valid orders found in file.")

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
                "profile_used": (
                    str(self._get_profile_path(customer_key))
                    if source_type == "csv"
                    else None
                ),
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