"""
rest_api_connector.py

REST API connector for the Modula WMS Data Integration Agent.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from src.ai.openai_client import OpenAIClient
from src.connectors.rate_limit_handler import RateLimitHandler
from src.connectors.request_body_builder import RequestBodyBuilder


def clean_json_response(response_text: str) -> str:
    cleaned = response_text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned.replace("```json", "", 1)

    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```", "", 1)

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return cleaned.strip()


class RestApiConnector:
    """
    REST API connector and API documentation analyzer.
    """

    def __init__(self):
        self.openai_client = OpenAIClient()
        self.rate_limit_handler = RateLimitHandler()
        self.request_body_builder = RequestBodyBuilder()

    def analyze_api_documentation(self, documentation_text: str) -> Dict:
        prompt = f"""
You are a warehouse integration expert.

Analyze the following API documentation.

Determine:

1. Which endpoint most likely contains order data
2. Which fields map to:
   - order_id
   - customer_name
   - item
   - quantity

Return ONLY valid JSON.

JSON format:

{{
    "source_type": "rest_api",
    "order_endpoint": "",
    "field_mapping": {{
        "order_id": "",
        "customer_name": "",
        "item": "",
        "quantity": ""
    }},
    "confidence_score": 0,
    "notes": []
}}

API Documentation:

{documentation_text[:12000]}
"""

        response = self.openai_client.ask(prompt)
        cleaned = clean_json_response(response)

        try:
            result = json.loads(cleaned)
            result["status"] = "success"
            return result
        except json.JSONDecodeError:
            return {
                "status": "error",
                "source_type": "rest_api",
                "message": "OpenAI returned invalid JSON.",
                "raw_response": response,
            }

    def build_headers(
        self,
        headers: Optional[dict[str, str]] = None,
        api_key: Optional[str] = None,
        api_key_header: str = "Authorization",
        bearer_token: bool = True,
    ) -> dict[str, str]:
        request_headers = headers.copy() if headers else {}

        if api_key:
            if bearer_token:
                request_headers[api_key_header] = f"Bearer {api_key}"
            else:
                request_headers[api_key_header] = api_key

        return request_headers

    def request_with_retries(
        self,
        method,
        url: str,
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, Any]] = None,
        json_body: Optional[Any] = None,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_seconds: int = 2,
    ) -> requests.Response:
        self.rate_limit_handler.max_retries = max_retries
        self.rate_limit_handler.base_delay_seconds = backoff_seconds

        request_kwargs = {
            "headers": headers,
            "params": params,
            "timeout": timeout,
        }

        if json_body is not None:
            request_kwargs["json"] = json_body

        return self.rate_limit_handler.run_with_retries(
            method,
            url,
            **request_kwargs,
        )

    def get_json(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        api_key: str | None = None,
        api_key_header: str = "Authorization",
        bearer_token: bool = True,
        timeout: int = 30,
        output_path: str | None = None,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        request_headers = self.build_headers(
            headers=headers,
            api_key=api_key,
            api_key_header=api_key_header,
            bearer_token=bearer_token,
        )

        try:
            response = self.request_with_retries(
                method=requests.get,
                url=url,
                headers=request_headers,
                params=params,
                timeout=timeout,
                max_retries=max_retries,
            )

            return self._build_json_result(response, url, output_path)

        except Exception as error:
            return {
                "status": "error",
                "source_type": "rest_api",
                "message": "REST API GET request failed.",
                "url": url,
                "error": str(error),
            }

    def post_json(
        self,
        url: str,
        json_body: dict | list,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        api_key: str | None = None,
        api_key_header: str = "Authorization",
        bearer_token: bool = True,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        request_headers = self.build_headers(
            headers=headers,
            api_key=api_key,
            api_key_header=api_key_header,
            bearer_token=bearer_token,
        )

        try:
            response = self.request_with_retries(
                method=requests.post,
                url=url,
                headers=request_headers,
                params=params,
                json_body=json_body,
                timeout=timeout,
                max_retries=max_retries,
            )

            return self._build_json_result(response, url)

        except Exception as error:
            return {
                "status": "error",
                "source_type": "rest_api",
                "message": "REST API POST request failed.",
                "url": url,
                "error": str(error),
            }

    def put_json(
        self,
        url: str,
        json_body: dict | list,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        api_key: str | None = None,
        api_key_header: str = "Authorization",
        bearer_token: bool = True,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        request_headers = self.build_headers(
            headers=headers,
            api_key=api_key,
            api_key_header=api_key_header,
            bearer_token=bearer_token,
        )

        try:
            response = self.request_with_retries(
                method=requests.put,
                url=url,
                headers=request_headers,
                params=params,
                json_body=json_body,
                timeout=timeout,
                max_retries=max_retries,
            )

            return self._build_json_result(response, url)

        except Exception as error:
            return {
                "status": "error",
                "source_type": "rest_api",
                "message": "REST API PUT request failed.",
                "url": url,
                "error": str(error),
            }

    def push_record(
        self,
        url: str,
        source_record: dict,
        field_mapping: dict,
        method: str = "POST",
        headers: dict[str, str] | None = None,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        json_body = self.request_body_builder.build_body(
            source_record=source_record,
            field_mapping=field_mapping,
        )

        if method.upper() == "PUT":
            return self.put_json(
                url=url,
                json_body=json_body,
                headers=headers,
                api_key=api_key,
            )

        return self.post_json(
            url=url,
            json_body=json_body,
            headers=headers,
            api_key=api_key,
        )

    def push_batch(
        self,
        url: str,
        source_records: list[dict],
        field_mapping: dict,
        batch_key: str | None = None,
        method: str = "POST",
        headers: dict[str, str] | None = None,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        json_body = self.request_body_builder.build_batch_body(
            source_records=source_records,
            field_mapping=field_mapping,
            batch_key=batch_key,
        )

        if method.upper() == "PUT":
            return self.put_json(
                url=url,
                json_body=json_body,
                headers=headers,
                api_key=api_key,
            )

        return self.post_json(
            url=url,
            json_body=json_body,
            headers=headers,
            api_key=api_key,
        )

    def get_paginated_json(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        api_key: str | None = None,
        api_key_header: str = "Authorization",
        bearer_token: bool = True,
        timeout: int = 30,
        page_param: str = "page",
        per_page_param: str = "per_page",
        start_page: int = 1,
        per_page: int = 100,
        max_pages: int = 50,
        records_key: str | None = None,
        output_path: str | None = None,
    ) -> dict[str, Any]:
        all_records: List[Any] = []
        current_page = start_page

        request_headers = self.build_headers(
            headers=headers,
            api_key=api_key,
            api_key_header=api_key_header,
            bearer_token=bearer_token,
        )

        try:
            while current_page < start_page + max_pages:
                request_params = params.copy() if params else {}
                request_params[page_param] = current_page
                request_params[per_page_param] = per_page

                response = self.request_with_retries(
                    method=requests.get,
                    url=url,
                    headers=request_headers,
                    params=request_params,
                    timeout=timeout,
                )

                try:
                    data = response.json()
                except ValueError:
                    return {
                        "status": "error",
                        "source_type": "rest_api",
                        "message": "API response was not valid JSON.",
                        "url": url,
                        "status_code": response.status_code,
                        "raw_response": response.text[:2000],
                    }

                if records_key:
                    records = data.get(records_key, [])
                else:
                    records = data

                if not isinstance(records, list):
                    return {
                        "status": "error",
                        "source_type": "rest_api",
                        "message": "Paginated response did not contain a list of records.",
                        "url": url,
                        "records_key": records_key,
                        "page": current_page,
                    }

                if not records:
                    break

                all_records.extend(records)

                if len(records) < per_page:
                    break

                current_page += 1

            result = {
                "status": "success",
                "source_type": "rest_api",
                "url": url,
                "pagination_type": "page_per_page",
                "pages_loaded": current_page - start_page + 1,
                "records_loaded": len(all_records),
                "data": all_records,
            }

            if output_path:
                path = Path(output_path)
                path.parent.mkdir(parents=True, exist_ok=True)

                with open(path, "w", encoding="utf-8") as file:
                    json.dump(result, file, indent=4)

                result["output_path"] = str(path)

            return result

        except Exception as error:
            return {
                "status": "error",
                "source_type": "rest_api",
                "message": "Paginated REST API GET request failed.",
                "url": url,
                "error": str(error),
            }

    def _build_json_result(
        self,
        response: requests.Response,
        url: str,
        output_path: str | None = None,
    ) -> dict[str, Any]:
        try:
            data = response.json()
        except ValueError:
            data = response.text[:2000]

        result = {
            "status": "success",
            "source_type": "rest_api",
            "url": url,
            "status_code": response.status_code,
            "data": data,
        }

        if output_path:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as file:
                json.dump(result, file, indent=4)

            result["output_path"] = str(path)

        return result