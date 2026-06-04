import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.integration_agent import (
    process_csv_files,
    process_json_file,
)

from tools.tool_registry import TOOLS


def customer_profile_exists(customer_name: str):
    safe_name = customer_name.lower().replace(" ", "_")

    profile_path = (
        Path("configs/customers")
        / f"{safe_name}_profile.json"
    )

    return profile_path.exists(), str(profile_path)


def process_customer_files(
    customer_name: str,
    file_paths: list[str],
):
    exists, profile_path = customer_profile_exists(
        customer_name
    )

    if exists:
        print(f"\nExisting customer found: {customer_name}")

        result = TOOLS["convert_existing_customer_files"](
            profile_path,
            file_paths,
        )

        return {
            "customer_exists": True,
            "profile_path": profile_path,
            "result": result,
        }

    print(
        f"\nNew customer detected: "
        f"{customer_name}"
    )

    if not file_paths:
        raise ValueError(
            "No input files were provided."
        )

    extensions = [
        Path(file).suffix.lower()
        for file in file_paths
    ]

    # Single CSV file
    if (
        len(file_paths) == 1
        and extensions[0] == ".csv"
    ):
        result = process_csv_files(
            file_paths[0],
            None,
            customer_name,
        )

    # Header + Line CSV files
    elif (
        len(file_paths) == 2
        and all(ext == ".csv" for ext in extensions)
    ):
        result = process_csv_files(
            file_paths[0],
            file_paths[1],
            customer_name,
        )

    # Single JSON file
    elif (
        len(file_paths) == 1
        and extensions[0] == ".json"
    ):
        result = process_json_file(
            file_paths[0],
            customer_name,
        )

    else:
        raise ValueError(
            f"Unsupported input: {file_paths}"
        )

    return {
        "customer_exists": False,
        "result": result,
    }


if __name__ == "__main__":

    result = process_customer_files(
        "Ford",
        [
            "data/sample_files/test_ui_headers.csv",
            "data/sample_files/test_ui_lines.csv",
        ],
    )

    print("\nResult:")
    print(result)