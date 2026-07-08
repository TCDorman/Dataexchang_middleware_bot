from models.endpoint_models import EndpointSchema


class EndpointDiscovery:
    """
    Lists and selects discovered REST API endpoints.
    """

    def list_endpoints(self, endpoints: list[EndpointSchema]) -> list[dict]:
        return [
            {
                "path": endpoint.path,
                "method": endpoint.method,
                "summary": endpoint.summary,
                "field_count": len(endpoint.response_fields),
            }
            for endpoint in endpoints
        ]

    def find_by_path(
        self,
        endpoints: list[EndpointSchema],
        path: str,
    ) -> EndpointSchema | None:
        for endpoint in endpoints:
            if endpoint.path == path:
                return endpoint

        return None