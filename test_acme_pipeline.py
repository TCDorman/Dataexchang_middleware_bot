from src.pipeline.file_processing_pipeline import FileProcessingPipeline

pipeline = FileProcessingPipeline()

result = pipeline.process_file(
    "data/customer_input/acme_orders.csv"
)

print("Profile Used:", result["profile_used"])
print("Orders Loaded:", result["orders_loaded"])
print("Decision:", result["decision"])
print("Export Result:", result["export_result"])