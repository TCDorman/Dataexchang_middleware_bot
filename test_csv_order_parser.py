"""
test_csv_order_parser.py

Manual test for CsvOrderParser.
"""

from src.parsing.csv_order_parser import CsvOrderParser

parser = CsvOrderParser()

orders = parser.parse("data/customer_input/test_orders.csv")

print(orders)