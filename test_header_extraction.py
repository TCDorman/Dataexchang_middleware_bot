from src.ai.header_extraction_agent import HeaderExtractionAgent


agent = HeaderExtractionAgent()

headers = agent.extract_headers(
    "data/customer_input/testfile.csv"
)

print(headers)