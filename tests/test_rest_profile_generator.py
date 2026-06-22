from agents.rest_profile_generator import save_rest_profile

path = save_rest_profile(
    customer_name="Test Customer",
    confirmed_mapping={
        "order_id": "id",
        "customer_name": "userId",
        "item": "title",
        "quantity": "body",
    },
)

print("REST PROFILE CREATED")
print("=" * 50)
print(path)