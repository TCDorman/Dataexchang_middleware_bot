"""
test_process_file.py

Tests the full file processing pipeline.

This simulates how the final application will process
customer files.
"""

from src.pipeline.file_processing_pipeline import FileProcessingPipeline

pipeline = FileProcessingPipeline()

result = pipeline.process_file(
    "data/customer_input/test_orders.csv"
)

print("Source File:", result["source_file"])
print("Orders Loaded:", result["orders_loaded"])
print("Workflow Status:", result["status"])
print("Decision:", result["decision"])
print("Export Result:", result["export_result"])
print("Parser Used:", result.get("parser_used"))