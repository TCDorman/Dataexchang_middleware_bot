# src/connectors/response_normalizer.py

from models.endpoint_models import EndpointSchema


class ResponseNormalizer:
    """
    Converts REST endpoint schemas into the same simple field-list shape
    used by the existing mapping pipeline.
    """

    def normalize(self, endpoint_schema: EndpointSchema) -> dict:
        return {
            "source_type": "rest_api",
            "path": endpoint_schema.path,
            "method": endpoint_schema.method,
            "summary": endpoint_schema.summary,
            "fields": [
                {
                    "source_field": field.name,
                    "type": field.type,
                    "nullable": field.nullable,
                    "description": field.description,
                    "sample_value": field.sample_value,
                }
                for field in endpoint_schema.response_fields
            ],
        }