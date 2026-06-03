"""
test_file_processing_pipeline.py

Manual test for the FileProcessingPipeline.

This confirms that the pipeline can pass transformed orders into
the full workflow runner.
"""

from src.pipeline.file_processing_pipeline import FileProcessingPipeline

pipeline = FileProcessingPipeline()

orders = [
    {
        "order_id": "ORD-1001",
        "customer_name": "Ford",
        "lines": [
            {"item": "ABC123", "quantity": 5},
        ],
    }
]

result = pipeline.process_transformed_orders(orders)

print("Pipeline Status:", result["status"])
print("Decision:", result["decision"])
print("Export Result:", result["export_result"])
print("History Record:", result["history_record"])