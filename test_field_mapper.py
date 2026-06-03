from src.profiles.field_mapper import FieldMapper
from src.profiles.profile_loader import ProfileLoader

loader = ProfileLoader()
mapper = FieldMapper()

profile = loader.load_profile("ford")

customer_row = {
    "Order Number": "ORD-1001",
    "Customer": "Ford",
    "Part": "ABC123",
    "Qty": "5"
}

mapped_row = mapper.map_row(
    customer_row,
    profile
)

print(mapped_row)