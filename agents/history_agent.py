import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools.tool_registry import TOOLS


def show_integration_history(customer_name: str | None = None):
    entries = TOOLS["read_audit_log"]()

    if customer_name:
        entries = [
            entry for entry in entries
            if entry["customer_name"].lower() == customer_name.lower()
        ]

    return entries


if __name__ == "__main__":
    history = show_integration_history()

    print("\nINTEGRATION HISTORY")

    for entry in history:
        print(
            f"{entry['timestamp']} | "
            f"{entry['customer_name']} | "
            f"{entry['direction']} | "
            f"{entry['status']} | "
            f"{entry['output_file']}"
        )