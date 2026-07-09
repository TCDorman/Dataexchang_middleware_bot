"""
folder_watcher.py

Watches the customer input folder and automatically
processes new files.

Workflow:

customer_input/
        ↓
process file
        ↓
success -> processed/
failure -> failed/
"""

import shutil
import time
from pathlib import Path

from src.pipeline.file_processing_pipeline import FileProcessingPipeline


class FolderWatcher:
    """
    Watches a folder and processes incoming CSV files.
    """

    def __init__(
        self,
        input_dir: str = "data/customer_input",
        processed_dir: str = "data/processed",
        failed_dir: str = "data/failed",
    ):
        """
        Initialize watcher folders.
        """

        self.input_dir = Path(input_dir)
        self.processed_dir = Path(processed_dir)
        self.failed_dir = Path(failed_dir)

        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.failed_dir.mkdir(parents=True, exist_ok=True)

        self.pipeline = FileProcessingPipeline()

    def start(self):
        """
        Begin watching the folder.
        """

        print("=" * 60)
        print("MODULA FOLDER WATCHER STARTED")
        print("=" * 60)
        print(f"Watching folder: {self.input_dir}")
        print("Press Ctrl+C to stop.")
        print("=" * 60)

        while True:
            self._scan_folder()
            time.sleep(5)

    def _scan_folder(self):
        """
        Scan for CSV files in the input directory.
        """

        files = list(self.input_dir.glob("*.csv"))

        for file_path in files:
            self._process_file(file_path)

    def _process_file(
        self,
        file_path: Path,
    ):
        """
        Process one detected file.
        """

        print("\n" + "-" * 60)
        print(f"Detected file: {file_path.name}")
        print("-" * 60)

        try:
            result = self.pipeline.process_file(str(file_path))

            self._print_processing_result(result)

            if result.get("status") == "success":
                destination = self.processed_dir / file_path.name
                shutil.move(str(file_path), str(destination))
                print(f"Moved to processed folder: {destination}")

            else:
                destination = self.failed_dir / file_path.name
                shutil.move(str(file_path), str(destination))
                print(f"Moved to failed folder: {destination}")

        except Exception as error:
            destination = self.failed_dir / file_path.name
            shutil.move(str(file_path), str(destination))

            print(f"Unhandled watcher error. Moved to failed folder: {destination}")
            print(f"Error: {error}")

    def _print_processing_result(
        self,
        result: dict,
    ):
        """
        Print the important processing details so users can see
        which parser, profile, and output file were used.
        """

        print("Processing Result:")
        print(f"  Status: {result.get('status')}")
        print(f"  Source File: {result.get('source_file')}")
        print(f"  Profile Used: {result.get('profile_used')}")
        print(f"  Parser Used: {result.get('parser_used')}")
        print(f"  Orders Loaded: {result.get('orders_loaded')}")

        decision = result.get("decision", {})
        print("  Decision:")
        print(f"    Action: {decision.get('action')}")
        print(f"    Reason: {decision.get('reason')}")

        export_result = result.get("export_result", {})
        print("  Export:")
        print(f"    Status: {export_result.get('status')}")
        print(f"    Output Path: {export_result.get('output_path')}")
        print(f"    Orders Exported: {export_result.get('orders_exported')}")

        if result.get("error_message"):
            print("  Error:")
            print(f"    {result.get('error_message')}")