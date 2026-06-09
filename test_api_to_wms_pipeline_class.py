"""
==================================================
API To WMS Pipeline Class Test
==================================================
"""

from src.connectors.api_to_wms_pipeline import (
    ApiToWmsPipeline,
)


api_response = {
    "orders": [
        {
            "orderNo": "ORD-2001",
            "description": "Generated pipeline order",
            "type": "PICK",
            "items": [
                {
                    "sku": "XYZ789",
                    "qty": 3,
                }
            ],
        }
    ]
}

pipeline = ApiToWmsPipeline()

result = pipeline.process_response(
    api_response=api_response,
    mapping_path="generated_integrations/demo_erp/mapping.json",
    output_path="data/output/api_pipeline_class_test.xml",
)

print(result)