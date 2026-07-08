import json
from pathlib import Path

from models.endpoint_models import EndpointSchema, ResponseField


class SpecParser:
    def load_from_file(self, spec_path: str) -> dict:
        with open(Path(spec_path), "r", encoding="utf-8") as file:
            return json.load(file)

    def extract_endpoints(self, spec: dict) -> list[EndpointSchema]:
        endpoints = []

        for path, methods in spec.get("paths", {}).items():
            for method, details in methods.items():
                if method.lower() not in ["get", "post", "put", "patch", "delete"]:
                    continue

                endpoints.append(
                    EndpointSchema(
                        path=path,
                        method=method.upper(),
                        summary=details.get("summary", ""),
                        response_fields=self._extract_response_fields(spec, details),
                    )
                )

        return endpoints

    def _extract_response_fields(self, spec: dict, operation: dict) -> list[ResponseField]:
        responses = operation.get("responses", {})
        success_response = responses.get("200") or responses.get("201") or {}
        content = success_response.get("content", {})
        schema = content.get("application/json", {}).get("schema", {})
        resolved_schema = self._resolve_schema(spec, schema)
        return self._schema_to_fields(spec, resolved_schema)

    def _resolve_schema(self, spec: dict, schema: dict) -> dict:
        if "$ref" in schema:
            resolved = spec
            for part in schema["$ref"].replace("#/", "").split("/"):
                resolved = resolved.get(part, {})
            return resolved

        if schema.get("type") == "array":
            return self._resolve_schema(spec, schema.get("items", {}))

        return schema

    def _schema_to_fields(
        self,
        spec: dict,
        schema: dict,
        prefix: str = "",
    ) -> list[ResponseField]:
        fields = []

        for field_name, field_info in schema.get("properties", {}).items():
            full_name = f"{prefix}.{field_name}" if prefix else field_name
            field_info = self._resolve_schema(spec, field_info)

            if field_info.get("type") == "object":
                fields.extend(self._schema_to_fields(spec, field_info, full_name))
            else:
                fields.append(
                    ResponseField(
                        name=full_name,
                        type=field_info.get("type", "unknown"),
                        nullable=field_info.get("nullable", False),
                        description=field_info.get("description", ""),
                    )
                )

        return fields