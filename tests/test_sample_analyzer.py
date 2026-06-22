"""
test_sample_analyzer.py

Tests the SampleAnalyzer by analyzing a sample JSON payload
and printing the discovered endpoint schema and fields.
"""

from src.connectors.sample_analyzer import SampleAnalyzer


sample_payload = [
    {
        "orderId": "ORD-1001",
        "customer": {
            "name": "Ford",
            "id": "CUST-001",
        },
        "lines": [
            {
                "itemCode": "ABC123",
                "quantity": 5,
            }
        ],
    }
]

analyzer = SampleAnalyzer()
schema = analyzer.analyze(sample_payload)

print("SAMPLE ANALYZER TEST")
print("=" * 60)
print(f"Path: {schema.path}")
print(f"Method: {schema.method}")
print(f"Summary: {schema.summary}")
print("\nDiscovered Fields:")
print("-" * 60)

for field in schema.response_fields:
    print(
        f"Name: {field.name:<25} "
        f"Type: {field.type:<10} "
        f"Nullable: {field.nullable} "
        f"Sample: {field.sample_value}"
    )