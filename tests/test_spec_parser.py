from src.connectors.spec_parser import SpecParser


sample_spec = {
    "openapi": "3.0.0",
    "paths": {
        "/orders": {
            "get": {
                "summary": "Get orders",
                "responses": {
                    "200": {
                        "description": "Orders response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "orderId": {"type": "string"},
                                            "customerName": {"type": "string"},
                                            "itemCode": {"type": "string"},
                                            "quantity": {"type": "integer"},
                                        },
                                    },
                                }
                            }
                        },
                    }
                },
            }
        }
    },
}


parser = SpecParser()
endpoints = parser.extract_endpoints(sample_spec)

print("SPEC PARSER TEST")
print("=" * 60)

for endpoint in endpoints:
    print(f"Path: {endpoint.path}")
    print(f"Method: {endpoint.method}")
    print(f"Summary: {endpoint.summary}")
    print("\nResponse Fields:")

    for field in endpoint.response_fields:
        print(f"- {field.name} ({field.type})")