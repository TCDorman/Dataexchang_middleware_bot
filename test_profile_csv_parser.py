from src.parsing.csv_order_parser import CsvOrderParser
from src.profiles.profile_loader import ProfileLoader

loader = ProfileLoader()
parser = CsvOrderParser()

profile = loader.load_profile("ford")

orders = parser.parse(
    "data/customer_input/ford_profile_orders.csv",
    profile=profile,
)

print(orders)