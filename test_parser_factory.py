from src.parsing.parser_factory import ParserFactory

parser = ParserFactory.get_parser(
    "data/customer_input/test_orders.csv"
)

print(type(parser).__name__)