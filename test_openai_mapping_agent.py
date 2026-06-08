from agents.openai_mapping_agent import infer_mapping_with_openai

sample = {
    "OrderNumber": "1001",
    "Customer": "Ford",
    "PartNumber": "ABC123",
    "Qty": 5
}

result = infer_mapping_with_openai(sample)

print(result)