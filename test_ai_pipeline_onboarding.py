"""
test_ai_pipeline_onboarding.py

Creates a brand-new unknown customer CSV and processes it
through the AI onboarding pipeline.
"""

from pathlib import Path

from src.pipeline.file_processing_pipeline import FileProcessingPipeline


test_file_path = Path("data/customer_input/phase9_unknown.csv")

test_file_path.parent.mkdir(parents=True, exist_ok=True)

test_file_path.write_text(
    """ORDER_REF,CLIENT_ORG,PRODUCT_ID,UNITS_REQUESTED
P900,Phase9Co,ITEM-A,5
P900,Phase9Co,ITEM-B,2
P901,Phase9Co,ITEM-C,7
""",
    encoding="utf-8",
)

print("Created test file:")
print(test_file_path.read_text(encoding="utf-8"))

pipeline = FileProcessingPipeline()

result = pipeline.process_file(str(test_file_path))

print("\nPipeline Result:")
print(result)