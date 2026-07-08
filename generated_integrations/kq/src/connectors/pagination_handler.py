class PaginationHandler:
    """
    Handles simple REST API pagination strategies.
    """

    def fetch_all_pages(
        self,
        client,
        endpoint: str,
        strategy: str = "none",
        results_key: str | None = None,
        next_key: str = "next",
        page_param: str = "page",
        page_size_param: str = "limit",
        page_size: int = 100,
        max_pages: int = 10,
    ) -> list:
        if strategy == "none":
            payload = client.get(endpoint)
            return self._extract_records(payload, results_key)

        if strategy == "next_link":
            return self._fetch_next_link_pages(
                client=client,
                endpoint=endpoint,
                results_key=results_key,
                next_key=next_key,
                max_pages=max_pages,
            )

        if strategy == "page_number":
            return self._fetch_page_number_pages(
                client=client,
                endpoint=endpoint,
                results_key=results_key,
                page_param=page_param,
                page_size_param=page_size_param,
                page_size=page_size,
                max_pages=max_pages,
            )

        raise ValueError(f"Unsupported pagination strategy: {strategy}")

    def _extract_records(self, payload, results_key: str | None):
        if results_key and isinstance(payload, dict):
            payload = payload.get(results_key, [])

        if isinstance(payload, list):
            return payload

        return [payload]

    def _fetch_next_link_pages(
        self,
        client,
        endpoint: str,
        results_key: str | None,
        next_key: str,
        max_pages: int,
    ) -> list:
        records = []
        current_endpoint = endpoint

        for _ in range(max_pages):
            payload = client.get(current_endpoint)
            records.extend(self._extract_records(payload, results_key))

            if not isinstance(payload, dict):
                break

            next_endpoint = payload.get(next_key)

            if not next_endpoint:
                break

            current_endpoint = next_endpoint

        return records

    def _fetch_page_number_pages(
        self,
        client,
        endpoint: str,
        results_key: str | None,
        page_param: str,
        page_size_param: str,
        page_size: int,
        max_pages: int,
    ) -> list:
        records = []

        for page in range(1, max_pages + 1):
            separator = "&" if "?" in endpoint else "?"
            paged_endpoint = (
                f"{endpoint}{separator}"
                f"{page_param}={page}&{page_size_param}={page_size}"
            )

            payload = client.get(paged_endpoint)
            page_records = self._extract_records(payload, results_key)

            if not page_records:
                break

            records.extend(page_records)

            if len(page_records) < page_size:
                break

        return records