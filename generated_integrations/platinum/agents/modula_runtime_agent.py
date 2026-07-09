"""
modula_runtime_agent.py

Runtime layer for interacting with Modula WMS.

For now, this uses the folder-based WMS adapter.
Later, this can be replaced with real Modula UI automation,
API calls, or database integration without changing the rest
of the agent workflow.
"""

from pathlib import Path
from typing import Dict, List

from wms.folder_wms_adapter import FolderWMSAdapter


class ModulaRuntimeAgent:
    """
    Provides a clean interface for sending imports to Modula WMS
    and checking for exported ordini files.
    """

    def __init__(
        self,
        ordini_import_folder: str = "data/wms_imports/ordini",
        articoli_import_folder: str = "data/wms_imports/articoli",
        export_ordini_folder: str = "data/wms_exports",
    ):
        self.adapter = FolderWMSAdapter(
            ordini_import_folder=ordini_import_folder,
            articoli_import_folder=articoli_import_folder,
            export_ordini_folder=export_ordini_folder,
        )

    def import_ordini(self, xml_path: str) -> Dict:
        imported_path = self.adapter.import_ordini(xml_path)

        return {
            "status": "success",
            "document_type": "ordini",
            "source_xml_path": xml_path,
            "wms_import_path": str(imported_path),
        }

    def import_articoli(self, xml_path: str) -> Dict:
        imported_path = self.adapter.import_articoli(xml_path)

        return {
            "status": "success",
            "document_type": "articoli",
            "source_xml_path": xml_path,
            "wms_import_path": str(imported_path),
        }

    def list_export_ordini_files(self) -> List[str]:
        files = self.adapter.list_export_ordini_files()
        return [str(path) for path in files]

    def get_status(self) -> Dict:
        return {
            "status": "ready",
            "adapter": "FolderWMSAdapter",
        }