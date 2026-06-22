"""
folder_wms_adapter.py

Folder-based WMS adapter.

This simulates or supports a WMS setup where XML import files
are dropped into import folders and export ordini files are read
from an export folder.
"""

import shutil
from pathlib import Path
from typing import List

from wms.wms_adapter import WMSAdapter


class FolderWMSAdapter(WMSAdapter):
    def __init__(
        self,
        ordini_import_folder: str,
        articoli_import_folder: str,
        export_ordini_folder: str,
    ):
        self.ordini_import_folder = Path(ordini_import_folder)
        self.articoli_import_folder = Path(articoli_import_folder)
        self.export_ordini_folder = Path(export_ordini_folder)

        self.ordini_import_folder.mkdir(parents=True, exist_ok=True)
        self.articoli_import_folder.mkdir(parents=True, exist_ok=True)
        self.export_ordini_folder.mkdir(parents=True, exist_ok=True)

    def import_ordini(self, xml_path: str) -> Path:
        source = Path(xml_path)

        if not source.exists():
            raise FileNotFoundError(f"Ordini XML not found: {source}")

        destination = self.ordini_import_folder / source.name
        shutil.copy2(source, destination)

        return destination

    def import_articoli(self, xml_path: str) -> Path:
        source = Path(xml_path)

        if not source.exists():
            raise FileNotFoundError(f"Articoli XML not found: {source}")

        destination = self.articoli_import_folder / source.name
        shutil.copy2(source, destination)

        return destination

    def list_export_ordini_files(self) -> List[Path]:
        supported_extensions = {
            ".json",
            ".xml",
            ".csv",
        }

        return [
            path
            for path in sorted(self.export_ordini_folder.iterdir())
            if path.is_file() and path.suffix.lower() in supported_extensions
        ]