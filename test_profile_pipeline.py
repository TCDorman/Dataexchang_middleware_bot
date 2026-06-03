"""
test_profile_pipeline.py

Tests the profile-aware file processing pipeline.
"""

from src.pipeline.file_processing_pipeline import (
    FileProcessingPipeline,
)

pipeline = FileProcessingPipeline()

result = pipeline.process_file(
    "data/customer_input/ford_profile_orders.csv"
)

print("Profile Used:", result["profile_used"])
print("Orders Loaded:", result["orders_loaded"])
print("Decision:", result["decision"])
print("Export Result:", result["export_result"])