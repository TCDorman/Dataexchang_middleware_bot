"""
main.py

Command-line entry point for the Modula WMS Data Integration Agent.
"""

import sys

from src.ai.validation_explanation_agent import ValidationExplanationAgent
from src.pipeline.file_processing_pipeline import FileProcessingPipeline


def process_file(file_path: str) -> None:
    """
    Process a customer file.

    Args:
        file_path: Path to customer input file.
    """

    pipeline = FileProcessingPipeline()
    result = pipeline.process_file(file_path)

    print("\n" + "=" * 60)
    print("MODULA WMS DATA INTEGRATION AGENT")
    print("=" * 60)

    print(f"Status: {result.get('status')}")
    print(f"Source File: {result.get('source_file')}")
    print(f"Profile Used: {result.get('profile_used')}")
    print(f"Orders Loaded: {result.get('orders_loaded')}")

    decision = result.get("decision", {})
    print("\nDecision:")
    print(f"  Action: {decision.get('action')}")
    print(f"  Reason: {decision.get('reason')}")

    export_result = result.get("export_result", {})
    print("\nExport:")
    print(f"  Status: {export_result.get('status')}")
    print(f"  Output Path: {export_result.get('output_path')}")
    print(f"  Orders Exported: {export_result.get('orders_exported')}")

    history_record = result.get("history_record")
    if history_record:
        print("\nHistory:")
        print(f"  Timestamp: {history_record.get('timestamp')}")
        print("  Transaction recorded successfully.")

    if result.get("status") != "success":
        print("\nAI Explanation:")
        explanation_agent = ValidationExplanationAgent()
        explanation = explanation_agent.explain_validation_result(result)
        print(explanation)

    print("=" * 60)


def main() -> None:
    """
    CLI entry point.
    """

    if len(sys.argv) < 3:
        print("\nUsage:")
        print("python main.py process <file_path>")
        return

    command = sys.argv[1].lower()

    if command == "process":
        process_file(sys.argv[2])
        return

    print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()