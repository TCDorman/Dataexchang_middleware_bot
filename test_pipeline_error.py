from src.pipeline.file_processing_pipeline import FileProcessingPipeline

pipeline = FileProcessingPipeline()

result = pipeline.process_file(
    "data/customer_input/unknown_orders.csv"
)

print(result)