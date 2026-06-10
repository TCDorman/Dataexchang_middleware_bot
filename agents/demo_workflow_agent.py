"""
demo_workflow_agent.py

One-click demo workflow for the Modula WMS Data Integration Agent.
"""

import csv
from pathlib import Path

from agents.full_ai_onboarding_runner import run_full_ai_onboarding


def run_demo_workflow() -> dict:
    demo_folder = Path("data") / "demo"
    demo_folder.mkdir(parents=True, exist_ok=True)

    demo_file = demo_folder / "demo_orders.csv"

    demo_rows = [
        {
            "OrderID": "DEMO-1001",
            "CustomerName": "Ford",
            "Item": "ABC123",
            "Quantity": "5",
        },
        {
            "OrderID": "DEMO-1001",
            "CustomerName": "Ford",
            "Item": "XYZ789",
            "Quantity": "2",
        },
        {
            "OrderID": "DEMO-1002",
            "CustomerName": "GM",
            "Item": "LMN456",
            "Quantity": "10",
        },
    ]

    with open(demo_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["OrderID", "CustomerName", "Item", "Quantity"],
        )
        writer.writeheader()
        writer.writerows(demo_rows)

    result = run_full_ai_onboarding(
        customer_name="Demo Customer",
        source_type="csv",
        file_path=str(demo_file),
    )

    return {
        "status": "success",
        "message": "Demo workflow completed successfully.",
        "demo_file": str(demo_file),
        "result": result,
    }