# src/connectors/api_client.py

import requests
from requests.auth import HTTPBasicAuth


class APIClient:
    def __init__(
        self,
        base_url: str,
        auth_type: str = "none",
        api_key: str | None = None,
        api_key_header: str = "Authorization",
        bearer_token: str | None = None,
        username: str | None = None,
        password: str | None = None,
        timeout: int = 30,
        default_headers: dict | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.auth_type = auth_type
        self.api_key = api_key
        self.api_key_header = api_key_header
        self.bearer_token = bearer_token
        self.username = username
        self.password = password
        self.timeout = timeout
        self.session = requests.Session()

        if default_headers:
            self.session.headers.update(default_headers)

        self._apply_auth()

    def _apply_auth(self):
        if self.auth_type == "none":
            return

        if self.auth_type == "api_key":
            if not self.api_key:
                raise ValueError("API key auth requires an api_key.")

            self.session.headers.update({
                self.api_key_header: self.api_key
            })
            return

        if self.auth_type == "bearer":
            if not self.bearer_token:
                raise ValueError("Bearer auth requires a bearer_token.")

            self.session.headers.update({
                "Authorization": f"Bearer {self.bearer_token}"
            })
            return

        if self.auth_type == "basic":
            if not self.username or not self.password:
                raise ValueError("Basic auth requires username and password.")

            self.session.auth = HTTPBasicAuth(
                self.username,
                self.password,
            )
            return

        raise ValueError(f"Unsupported auth_type: {self.auth_type}")

    def request(self, method: str, endpoint: str, **kwargs):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        response = self.session.request(
            method=method.upper(),
            url=url,
            timeout=self.timeout,
            **kwargs,
        )

        response.raise_for_status()

        try:
            return response.json()
        except ValueError:
            return response.text

    def get(self, endpoint: str, **kwargs):
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs):
        return self.request("POST", endpoint, **kwargs)

    def get_openapi_document(self):
        """
        Try common OpenAPI/Swagger endpoints.
        """

        candidates = [
            "/openapi.json",
            "/swagger.json",
            "/api/openapi.json",
            "/api/swagger.json",
        ]

        for endpoint in candidates:
            try:
                result = self.get(endpoint)

                if isinstance(result, dict) and (
                    "openapi" in result or "swagger" in result
                ):
                    return result

            except Exception:
                continue

        return None