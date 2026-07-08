# src/connectors/wms_file_connector.py

from pathlib import Path
import shutil
from datetime import datetime


class WMSFileConnector:
    """
    Sends exported Ordini XML files to the WMS inbound folder.
    """

    def __init__(self, wms_inbound_folder: str):
        self.wms_inbound_folder = Path(wms_inbound_folder)

    def send_file(self, xml_file_path: str) -> dict:
        source_path = Path(xml_file_path)

        if not source_path.exists():
            return {
                "status": "error",
                "message": "XML file does not exist.",
                "source_path": str(source_path),
            }

        self.wms_inbound_folder.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        destination_path = self.wms_inbound_folder / f"{source_path.stem}_{timestamp}.xml"

        shutil.copy2(source_path, destination_path)

        return {
            "status": "success",
            "message": "XML file sent to WMS inbound folder.",
            "source_path": str(source_path),
            "destination_path": str(destination_path),
        }