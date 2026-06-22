"""
wms_adapter.py

Base interface for WMS import/export behavior.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List


class WMSAdapter(ABC):
    @abstractmethod
    def import_ordini(self, xml_path: str) -> Path:
        pass

    @abstractmethod
    def import_articoli(self, xml_path: str) -> Path:
        pass

    @abstractmethod
    def list_export_ordini_files(self) -> List[Path]:
        pass