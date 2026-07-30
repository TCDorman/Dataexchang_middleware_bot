"""
rate_limit_handler.py

Handles REST API rate limits and retry behavior.
"""

import time
from typing import Callable, Any


class RateLimitHandler:
    """
    Retries API calls when rate limits or temporary server errors occur.
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay_seconds: int = 2,
    ):
        self.max_retries = max_retries
        self.base_delay_seconds = base_delay_seconds

    def run_with_retries(
        self,
        request_function: Callable,
        *args,
        **kwargs,
    ) -> Any:
        attempt = 0

        while True:
            response = request_function(*args, **kwargs)

            status_code = getattr(response, "status_code", None)

            if status_code == 429:
                if attempt >= self.max_retries:
                    response.raise_for_status()

                retry_after = response.headers.get("Retry-After")

                if retry_after and retry_after.isdigit():
                    delay = int(retry_after)
                else:
                    delay = self.base_delay_seconds * (2 ** attempt)

                time.sleep(delay)
                attempt += 1
                continue

            if status_code is not None and 500 <= status_code < 600:
                if attempt >= self.max_retries:
                    response.raise_for_status()

                delay = self.base_delay_seconds * (2 ** attempt)
                time.sleep(delay)
                attempt += 1
                continue

            if hasattr(response, "raise_for_status"):
                response.raise_for_status()

            return response