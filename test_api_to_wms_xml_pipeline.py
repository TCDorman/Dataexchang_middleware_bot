"""
==================================================
API To WMS XML Pipeline Test
==================================================

Purpose:
    Test complete API integration flow:

    API Response
        ↓
    API Response Mapper
        ↓
    Validation Manager
        ↓
    WMSOrder Model Adapter
        ↓
    WMS XML Export
"""

# ==================================================
# Imports
# ==================================================

import json

from src.connectors.api_order_model_adapter import (
    ApiOrderModelAdapter,
)
from src.connectors.api_response_mapper import (
    ApiResponseMapper,
)
from src.validation.validation_manager import (
    ValidationManager,
)
from transformers.wms_xml_transformer import (
    export_orders_to_xml,
)


# ==================================================
# Sample API Response
# ==================================================

api_response = {
    "orders": [
        {
            "orderNo": "ORD-1001",
            "description": "Customer order",
            "type": "PICK",
            "items": [
                {
                    "sku": "ABC123",
                    "qty": 5,
                }
            ],
        }
    ]
}


# ==================================================
# Load Generated Mapping
# ==================================================

with open(
    "generated_integrations/demo_erp/mapping.json",
    "r",
    encoding="utf-8",
) as file:
    mapping_config = json.load(file)


# ==================================================
# Map API Response
# ==================================================

mapper = ApiResponseMapper()

orders = mapper.map_response(
    api_response,
    mapping_config,
)

print("\nNORMALIZED ORDERS")
print(orders)


# ==================================================
# Validate Orders
# ==================================================

validation_manager = ValidationManager()

validation_result = validation_manager.validate_orders(
    orders
)

print("\nVALIDATION RESULT")
print(validation_result)

if not validation_result["is_valid"]:
    raise ValueError(
        f"Validation failed: {validation_result['errors']}"
    )


# ==================================================
# Convert Dictionaries To WMS Models
# ==================================================

adapter = ApiOrderModelAdapter()

wms_orders = adapter.convert_orders(
    orders
)

print("\nWMS MODEL ORDERS")
print(wms_orders)


# ==================================================
# Export To XML
# ==================================================

output_path = "data/output/api_pipeline_test.xml"

export_orders_to_xml(
    wms_orders,
    output_path,
)

print("\nXML GENERATED")
print(output_path)