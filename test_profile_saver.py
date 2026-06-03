from src.profiles.profile_saver import ProfileSaver

saver = ProfileSaver()

profile = {
    "customer_name": "Test Customer",
    "header_signature": [
        "PO_NUM",
        "CUSTOMER_NAME",
        "PART_NUMBER",
        "REQUESTED_QTY",
    ],
    "field_mapping": {
        "PO_NUM": "order_id",
        "CUSTOMER_NAME": "customer_name",
        "PART_NUMBER": "item",
        "REQUESTED_QTY": "quantity",
    },
}

result = saver.save_profile(
    "test_customer",
    profile,
)

print(result)