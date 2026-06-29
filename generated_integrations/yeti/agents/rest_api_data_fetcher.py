"""
rest_api_data_fetcher.py

Fetches records from a REST API with optional pagination support.
"""

from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests


def extract_records(
    response_json: Any,
    results_key: Optional[str] = None,
) -> List[Dict]:
    if results_key:
        records = response_json.get(results_key, [])
    else:
        records = response_json

    if isinstance(records, dict):
        return [records]

    if isinstance(records, list):
        return records

    return []


def build_headers(
    auth_type: str = "none",
    api_key: Optional[str] = None,
    api_key_header: str = "Authorization",
    bearer_token: Optional[str] = None,
) -> Dict[str, str]:
    headers = {}

    if auth_type == "api_key" and api_key:
        headers[api_key_header] = api_key

    elif auth_type == "bearer" and bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"

    return headers


def fetch_rest_api_records(
    base_url: str,
    endpoint: str,
    auth_type: str = "none",
    api_key: Optional[str] = None,
    api_key_header: str = "Authorization",
    bearer_token: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    pagination_strategy: str = "none",
    results_key: Optional[str] = None,
    max_pages: int = 10,
    timeout_seconds: int = 30,
) -> Dict:
    records = []

    headers = build_headers(
        auth_type=auth_type,
        api_key=api_key,
        api_key_header=api_key_header,
        bearer_token=bearer_token,
    )

    auth = None
    if auth_type == "basic" and username and password:
        auth = (username, password)

    url = urljoin(base_url.rstrip("/") + "/", endpoint.lstrip("/"))

    try:
        if pagination_strategy == "none":
            response = requests.get(
                url,
                headers=headers,
                auth=auth,
                timeout=timeout_seconds,
            )
            response.raise_for_status()

            response_json = response.json()
            records.extend(extract_records(response_json, results_key))

        elif pagination_strategy == "page_number":
            for page_number in range(1, max_pages + 1):
                response = requests.get(
                    url,
                    headers=headers,
                    auth=auth,
                    params={"page": page_number},
                    timeout=timeout_seconds,
                )
                response.raise_for_status()

                response_json = response.json()
                page_records = extract_records(response_json, results_key)

                if not page_records:
                    break

                records.extend(page_records)

        elif pagination_strategy == "next_link":
            next_url = url
            pages_fetched = 0

            while next_url and pages_fetched < max_pages:
                response = requests.get(
                    next_url,
                    headers=headers,
                    auth=auth,
                    timeout=timeout_seconds,
                )
                response.raise_for_status()

                response_json = response.json()
                page_records = extract_records(response_json, results_key)
                records.extend(page_records)

                next_url = response_json.get("next")
                pages_fetched += 1

        else:
            return {
                "status": "error",
                "message": f"Unsupported pagination strategy: {pagination_strategy}",
                "records": [],
            }

        return {
            "status": "success",
            "records_fetched": len(records),
            "records": records,
        }

    except Exception as error:
        return {
            "status": "error",
            "message": "REST API fetch failed.",
            "error": str(error),
            "records": [],
        }