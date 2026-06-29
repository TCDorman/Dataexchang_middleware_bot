# src/connectors/sample_analyzer.py

from models.endpoint_models import EndpointSchema, ResponseField


class SampleAnalyzer:
    def analyze(self, payload):
        if isinstance(payload, list) and payload:
            payload = payload[0]

        fields = []
        self._flatten(payload, fields)

        return EndpointSchema(
            path="sample_payload",
            method="GET",
            summary="Inferred from sample JSON payload",
            response_fields=fields,
        )

    def _flatten(self, value, fields, prefix=""):
        if isinstance(value, dict):
            for key, child in value.items():
                name = f"{prefix}.{key}" if prefix else key
                self._flatten(child, fields, name)

        elif isinstance(value, list):
            if value:
                self._flatten(value[0], fields, prefix)
            else:
                fields.append(ResponseField(
                    name=prefix,
                    type="array",
                ))

        else:
            fields.append(ResponseField(
                name=prefix,
                type=self._get_type(value),
                nullable=value is None,
                sample_value=value,
            ))

    def _get_type(self, value):
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int):
            return "integer"
        if isinstance(value, float):
            return "number"
        if value is None:
            return "null"
        return "string"