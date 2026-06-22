# tests/test_response_normalizer.py

from src.connectors.sample_analyzer import SampleAnalyzer
from src.connectors.response_normalizer import ResponseNormalizer


payload = [
    {
        "orderId": "ORD-1001",
        "customer": {"name": "Ford"},
        "lines": [{"itemCode": "ABC123", "quantity": 5}],
    }
]

schema = SampleAnalyzer().analyze(payload)
normalized = ResponseNormalizer().normalize(schema)

print("RESPONSE NORMALIZER TEST")
print("=" * 60)
print(normalized)