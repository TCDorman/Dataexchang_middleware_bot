"""
==================================================
API To WMS Pipeline
==================================================

Purpose:
    Converts customer API responses into Modula WMS XML.

Workflow:
    API Response
        ↓
    Mapping JSON
        ↓
    API Response Mapper
        ↓
    Validation Manager
        ↓
    WMS Model Adapter
        ↓
    WMS XML Export
"""

# ==================================================
# Imports
# ==================================================

import json
from typing import Dict

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
# API To WMS Pipeline
# ==================================================

class ApiToWmsPipeline:
    """
    Reusable API-to-WMS conversion pipeline.
    """

    def __init__(self):
        """
        Initialize pipeline components.
        """

        self.response_mapper = ApiResponseMapper()
        self.validation_manager = ValidationManager()
        self.model_adapter = ApiOrderModelAdapter()

    def process_response(
        self,
        api_response: Dict,
        mapping_path: str,
        output_path: str,
    ) -> Dict:
        """
        Process an API response into WMS XML.

        Args:
            api_response:
                Raw API JSON response.
            mapping_path:
                Path to generated mapping.json.
            output_path:
                XML output path.

        Returns:
            Processing result.
        """

        mapping_config = self._load_mapping(
            mapping_path
        )

        normalized_orders = self.response_mapper.map_response(
            api_response,
            mapping_config,
        )

        validation_result = (
            self.validation_manager.validate_orders(
                normalized_orders
            )
        )

        if not validation_result["is_valid"]:
            raise ValueError(
                "API order validation failed: "
                f"{validation_result['errors']}"
            )

        wms_orders = self.model_adapter.convert_orders(
            normalized_orders
        )

        export_orders_to_xml(
            wms_orders,
            output_path,
        )

        return {
            "status": "success",
            "orders_converted": len(wms_orders),
            "validation_result": validation_result,
            "output_path": output_path,
        }

    def _load_mapping(
        self,
        mapping_path: str,
    ) -> Dict:
        """
        Load generated mapping.json.
        """

        with open(
            mapping_path,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)