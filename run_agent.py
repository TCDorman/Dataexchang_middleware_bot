import argparse
import shutil
import time
from datetime import datetime
from pathlib import Path

from agents.customer_detection_agent import detect_customer_from_files

from agents.master_agent import (
    run_customer_import,
    run_wms_export,
)

from agents.history_agent import show_integration_history


# ==================================================
# Logging
# ==================================================
def write_log(
    customer_name: str,
    status: str,
    files: list,
    message: str,
):
    """
    Write a processing event to a daily integration log.

    Logs are stored in:
    logs/integration_YYYY_MM_DD.log
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"integration_{datetime.now():%Y_%m_%d}.log"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_entry = (
        f"\n{'=' * 60}\n"
        f"Timestamp: {timestamp}\n"
        f"Customer: {customer_name}\n"
        f"Status: {status}\n"
        f"Files:\n"
    )

    for file in files:
        log_entry += f"  - {file}\n"

    log_entry += f"\nMessage:\n{message}\n"

    with open(log_file, "a", encoding="utf-8") as file:
        file.write(log_entry)


# ==================================================
# File Discovery
# ==================================================
def get_input_files(input_dir: Path):
    """
    Return all files directly inside the input folder.

    Subfolders like processed/ and failed/ are ignored.
    """
    return [
        path
        for path in input_dir.iterdir()
        if path.is_file()
    ]


# ==================================================
# File Grouping
# ==================================================
def group_customer_files(files):
    """
    Group customer files before processing.

    Current behavior:
    - If one header CSV and one line CSV are found,
      process them together.
    - Otherwise, process each file individually.
    """
    csv_files = [
        file
        for file in files
        if file.suffix.lower() == ".csv"
    ]

    header_files = [
        file
        for file in csv_files
        if "header" in file.stem.lower()
        or "headers" in file.stem.lower()
    ]

    line_files = [
        file
        for file in csv_files
        if "line" in file.stem.lower()
        or "lines" in file.stem.lower()
    ]

    if len(header_files) == 1 and len(line_files) == 1:
        return [[header_files[0], line_files[0]]]

    return [[file] for file in files]


# ==================================================
# Customer Resolution
# ==================================================
def resolve_customer(customer_name, file_paths):
    """
    Determine which customer should be used for processing.

    If --customer was provided, use it.
    Otherwise, detect the customer from the file names.
    """
    if customer_name:
        return customer_name

    detected_customer = detect_customer_from_files(file_paths)

    if not detected_customer:
        raise ValueError(
            f"Could not detect customer from files: {file_paths}"
        )

    print(f"Detected customer: {detected_customer}")

    return detected_customer


# ==================================================
# File Movement
# ==================================================
def move_files(files, destination_dir: Path):
    """
    Move processed files into processed/ or failed/.

    If a file with the same name already exists in the
    destination folder, it is overwritten.
    """
    destination_dir.mkdir(parents=True, exist_ok=True)

    for file in files:
        destination = destination_dir / file.name

        if destination.exists():
            destination.unlink()

        shutil.move(str(file), str(destination))


# ==================================================
# Process Folder Once
# ==================================================
def process_folder(customer_name: str | None, input_dir: str):
    """
    Process all files currently sitting in the input folder.

    Workflow:
    1. Find files in the input directory
    2. Group related files if needed
    3. Detect customer if --customer was not provided
    4. Run the customer import workflow
    5. Move successful files to processed/
    6. Move failed files to failed/
    7. Write success/failure logs
    """
    input_path = Path(input_dir)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input folder does not exist: {input_path}"
        )

    files = get_input_files(input_path)

    if not files:
        raise ValueError(
            f"No files found in input folder: {input_path}"
        )

    file_groups = group_customer_files(files)

    results = []

    processed_dir = input_path / "processed"
    failed_dir = input_path / "failed"

    for file_group in file_groups:
        file_paths = [
            str(file)
            for file in file_group
        ]

        resolved_customer = customer_name or "UNKNOWN"

        try:
            resolved_customer = resolve_customer(
                customer_name,
                file_paths,
            )

            result = run_customer_import(
                resolved_customer,
                file_paths,
            )

            write_log(
                customer_name=resolved_customer,
                status="SUCCESS",
                files=file_paths,
                message=str(result),
            )

            move_files(file_group, processed_dir)

            results.append(
                {
                    "customer": resolved_customer,
                    "files": file_paths,
                    "status": "success",
                    "result": result,
                }
            )

        except Exception as error:
            write_log(
                customer_name=resolved_customer,
                status="FAILED",
                files=file_paths,
                message=str(error),
            )

            move_files(file_group, failed_dir)

            results.append(
                {
                    "customer": resolved_customer,
                    "files": file_paths,
                    "status": "failed",
                    "error": str(error),
                }
            )

    return results


# ==================================================
# Watch Folder Continuously
# ==================================================
def watch_folder(
    customer_name: str | None,
    input_dir: str,
    poll_interval: int = 10,
):
    """
    Continuously monitor a folder and process files
    whenever new customer files appear.

    Press CTRL + C in the terminal to stop watch mode.
    """
    print("\nWATCH MODE STARTED")
    print(f"Customer: {customer_name if customer_name else 'Auto-detect'}")
    print(f"Input Folder: {input_dir}")
    print(f"Polling Interval: {poll_interval} seconds")
    print("Press CTRL + C to stop.")

    while True:
        try:
            input_path = Path(input_dir)

            if not input_path.exists():
                raise FileNotFoundError(
                    f"Input folder does not exist: {input_path}"
                )

            files = get_input_files(input_path)

            if files:
                print(
                    f"\nDetected {len(files)} file(s). Processing..."
                )

                results = process_folder(
                    customer_name,
                    input_dir,
                )

                for result in results:
                    print(
                        f"{result['status'].upper()} | "
                        f"{result.get('customer')} | "
                        f"{result['files']}"
                    )

                    if result["status"] == "failed":
                        print(f"  Error: {result['error']}")

            time.sleep(poll_interval)

        except KeyboardInterrupt:
            print("\nWatch mode stopped.")
            break

        except Exception as error:
            print(f"\nWatch mode error: {error}")
            time.sleep(poll_interval)


# ==================================================
# Main CLI Entry Point
# ==================================================
def main():
    """
    Define and run the command-line interface for the
    Modula WMS Integration Agent.
    """
    parser = argparse.ArgumentParser(
        description="Modula WMS Integration Agent"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # ----------------------------------------------
    # Import Command
    # ----------------------------------------------
    import_parser = subparsers.add_parser(
        "import",
        help="Convert customer ERP data into Modula WMS XML",
    )

    import_parser.add_argument(
        "--customer",
        required=True,
        help="Customer name",
    )

    import_parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="Input customer files",
    )

    # ----------------------------------------------
    # Export Command
    # ----------------------------------------------
    export_parser = subparsers.add_parser(
        "export",
        help="Convert Modula WMS export XML into customer format",
    )

    export_parser.add_argument(
        "--wms-file",
        required=True,
        help="WMS export XML file",
    )

    export_parser.add_argument(
        "--output",
        default="data/output/customer_export.csv",
        help="Customer output file",
    )

    # ----------------------------------------------
    # History Command
    # ----------------------------------------------
    history_parser = subparsers.add_parser(
        "history",
        help="Show integration history",
    )

    history_parser.add_argument(
        "--customer",
        required=False,
        help="Optional customer filter",
    )

    # ----------------------------------------------
    # Process Folder Command
    # ----------------------------------------------
    folder_parser = subparsers.add_parser(
        "process-folder",
        help="Process all files in a customer input folder",
    )

    folder_parser.add_argument(
        "--customer",
        required=False,
        help="Customer name. If omitted, the agent will try to detect it.",
    )

    folder_parser.add_argument(
        "--input-dir",
        default="data/customer_input",
        help="Folder containing customer input files",
    )

    # ----------------------------------------------
    # Watch Folder Command
    # ----------------------------------------------
    watch_parser = subparsers.add_parser(
        "watch",
        help="Continuously monitor a folder for customer files",
    )

    watch_parser.add_argument(
        "--customer",
        required=False,
        help="Customer name. If omitted, the agent will try to detect it.",
    )

    watch_parser.add_argument(
        "--input-dir",
        default="data/customer_input",
        help="Folder to monitor",
    )

    watch_parser.add_argument(
        "--interval",
        type=int,
        default=10,
        help="Polling interval in seconds",
    )

    args = parser.parse_args()

    # ----------------------------------------------
    # Command Routing
    # ----------------------------------------------
    if args.command == "import":
        result = run_customer_import(
            args.customer,
            args.files,
        )

        print("\nIMPORT COMPLETE")
        print(result)

    elif args.command == "export":
        result = run_wms_export(
            args.wms_file,
            args.output,
        )

        print("\nEXPORT COMPLETE")
        print(result)

    elif args.command == "history":
        history = show_integration_history(args.customer)

        print("\nINTEGRATION HISTORY")

        for entry in history:
            print(
                f"{entry['timestamp']} | "
                f"{entry['customer_name']} | "
                f"{entry['direction']} | "
                f"{entry['status']} | "
                f"{entry['output_file']}"
            )

    elif args.command == "process-folder":
        results = process_folder(
            args.customer,
            args.input_dir,
        )

        print("\nFOLDER PROCESS COMPLETE")

        for result in results:
            print(
                f"{result['status'].upper()} | "
                f"{result.get('customer')} | "
                f"{result['files']}"
            )

            if result["status"] == "failed":
                print(f"  Error: {result['error']}")

    elif args.command == "watch":
        watch_folder(
            args.customer,
            args.input_dir,
            args.interval,
        )


if __name__ == "__main__":
    main()