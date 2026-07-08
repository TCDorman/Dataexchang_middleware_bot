import sys
from pathlib import Path
import shutil

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools.tool_registry import TOOLS
from agents.customer_router import process_customer_files


def move_files(file_paths: list[str], destination_folder: Path):
    destination_folder.mkdir(parents=True, exist_ok=True)

    moved_files = []

    for file_path in file_paths:
        source = Path(file_path)
        destination = destination_folder / source.name

        shutil.move(str(source), str(destination))
        moved_files.append(str(destination))

    return moved_files


def scan_customer_input_folder(customer_name: str):
    settings = TOOLS["load_local_settings"]()

    input_folder = Path(settings["customer_input_folder"])
    processed_folder = input_folder / "processed"
    failed_folder = input_folder / "failed"

    if not input_folder.exists():
        raise FileNotFoundError(f"Input folder not found: {input_folder}")

    files = [
        str(file)
        for file in input_folder.iterdir()
        if file.is_file()
    ]

    if not files:
        return {
            "status": "no_files",
            "message": f"No files found in {input_folder}",
        }

    csv_files = [
        file for file in files
        if file.lower().endswith(".csv")
    ]

    json_files = [
        file for file in files
        if file.lower().endswith(".json")
    ]

    try:
        if len(csv_files) >= 2:
            selected_files = csv_files[:2]

            result = process_customer_files(
                customer_name,
                selected_files,
            )

            moved_files = move_files(
                selected_files,
                processed_folder,
            )

            return {
                "status": "processed",
                "source_type": "csv",
                "files": selected_files,
                "moved_files": moved_files,
                "result": result,
            }

        if len(json_files) >= 1:
            selected_files = [json_files[0]]

            result = process_customer_files(
                customer_name,
                selected_files,
            )

            moved_files = move_files(
                selected_files,
                processed_folder,
            )

            return {
                "status": "processed",
                "source_type": "json",
                "files": selected_files,
                "moved_files": moved_files,
                "result": result,
            }

        return {
            "status": "unsupported",
            "files": files,
        }

    except Exception as error:
        move_files(files, failed_folder)

        return {
            "status": "failed",
            "error": str(error),
            "files": files,
        }


if __name__ == "__main__":
    result = scan_customer_input_folder("Ford")

    print("\nFolder Monitor Result:")
    print(result)