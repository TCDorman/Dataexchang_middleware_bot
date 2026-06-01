import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.integration_agent import (
    process_csv_files,
    process_json_file,
)


def run_workflow(file_paths: list[str]):
    extensions = [Path(file).suffix.lower() for file in file_paths]

    if len(file_paths) == 2 and all(ext == ".csv" for ext in extensions):
        return process_csv_files(
            file_paths[0],
            file_paths[1],
        )

    if len(file_paths) == 1 and extensions[0] == ".json":
        return process_json_file(
            file_paths[0],
        )

    raise ValueError(
        f"Unsupported workflow input: {file_paths}"
    )


if __name__ == "__main__":
    result = run_workflow(
        [
            "data/sample_files/test_ui_headers.csv",
            "data/sample_files/test_ui_lines.csv",
        ]
    )

    print("\nWorkflow Result:")
    print(result)