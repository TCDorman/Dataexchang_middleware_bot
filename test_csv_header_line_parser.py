from src.parsing.csv_header_line_parser import CsvHeaderLineParser

parser = CsvHeaderLineParser()

orders = parser.parse(
    "data/customer_input/pair_headers.csv",
    "data/customer_input/pair_lines.csv",
)

print(orders)