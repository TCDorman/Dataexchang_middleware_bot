from src.connectors.pagination_handler import PaginationHandler


class FakeClient:
    def get(self, endpoint):
        pages = {
            "/orders?page=1&limit=2": [
                {"orderNumber": "ORDER1"},
                {"orderNumber": "ORDER2"},
            ],
            "/orders?page=2&limit=2": [
                {"orderNumber": "ORDER3"},
            ],
        }

        return pages.get(endpoint, [])


handler = PaginationHandler()

records = handler.fetch_all_pages(
    client=FakeClient(),
    endpoint="/orders",
    strategy="page_number",
    page_size=2,
    max_pages=5,
)

print("PAGINATION HANDLER TEST")
print("=" * 60)
print(records)