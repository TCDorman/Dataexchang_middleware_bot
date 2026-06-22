from src.connectors.spec_parser import SpecParser
from src.connectors.endpoint_discovery import EndpointDiscovery


sample_spec = {
    "openapi": "3.0.0",
    "paths": {
        "/orders": {
            "get": {
                "summary": "Retrieve orders",
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "orderId": {"type": "string"},
                                        "customerName": {"type": "string"},
                                    },
                                }
                            }
                        }
                    }
                },
            }
        },
        "/inventory": {
            "get": {
                "summary": "Retrieve inventory",
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "itemCode": {"type": "string"},
                                        "quantity": {"type": "integer"},
                                    },
                                }
                            }
                        }
                    }
                },
            }
        },
    },
}


parser = SpecParser()
endpoints = parser.extract_endpoints(sample_spec)

discovery = EndpointDiscovery()

print("ENDPOINT DISCOVERY TEST")
print("=" * 60)

for endpoint in discovery.list_endpoints(endpoints):
    print(endpoint)

selected = discovery.find_by_path(endpoints, "/orders")

print("\nSELECTED ENDPOINT")
print("=" * 60)
print(selected)