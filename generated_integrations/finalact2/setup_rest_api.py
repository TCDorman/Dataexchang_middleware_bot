"""
setup_rest_api.py

Customer-friendly REST API setup utility.

Run from the generated package folder:
    python setup_rest_api.py

Or double-click:
    setup_api.bat

This script updates only the "rest_api" section of config.json.
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = PACKAGE_DIR / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing config.json: {CONFIG_PATH}")

    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def save_config(config: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=4)


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    default_label = "Y/n" if default else "y/N"

    while True:
        value = input(f"{prompt} [{default_label}]: ").strip().lower()

        if not value:
            return default

        if value in ["y", "yes"]:
            return True

        if value in ["n", "no"]:
            return False

        print("Please enter y or n.")


def ask_text(prompt: str, default: str = "") -> str:
    if default:
        value = input(f"{prompt} [{default}]: ").strip()
        return value or default

    return input(f"{prompt}: ").strip()


def ask_int(prompt: str, default: int) -> int:
    while True:
        value = input(f"{prompt} [{default}]: ").strip()

        if not value:
            return default

        try:
            return int(value)
        except ValueError:
            print("Please enter a whole number.")


def ask_json_object(prompt: str, default: dict | None = None) -> dict:
    default = default or {}

    print(prompt)
    print("Leave blank for {}.")

    while True:
        value = input("> ").strip()

        if not value:
            return default

        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as error:
            print(f"Invalid JSON: {error}")
            continue

        if not isinstance(parsed, dict):
            print("Please enter a JSON object, for example: {\"X-Header\": \"value\"}")
            continue

        return parsed


def build_headers(rest_config: dict) -> dict:
    headers = dict(rest_config.get("headers", {}) or {})
    api_key = rest_config.get("api_key", "")
    api_key_header = rest_config.get("api_key_header", "Authorization")
    bearer_token = bool(rest_config.get("bearer_token", True))

    if api_key:
        headers[api_key_header] = f"Bearer {api_key}" if bearer_token else api_key

    return headers


def test_get(url: str, rest_config: dict) -> None:
    if not url:
        print("Import URL is blank; skipping GET test.")
        return

    params = rest_config.get("params", {}) or {}
    query = urllib.parse.urlencode(params)
    test_url = f"{url}?{query}" if query else url

    request = urllib.request.Request(
        test_url,
        method="GET",
        headers=build_headers(rest_config),
    )

    timeout = int(rest_config.get("timeout_seconds", 30))

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(500).decode("utf-8", errors="replace")
            print(f"GET test succeeded. HTTP {response.status}")
            print(f"Response preview: {body}")
    except urllib.error.HTTPError as error:
        print(f"GET test failed. HTTP {error.code}: {error.reason}")
    except Exception as error:
        print(f"GET test failed: {error}")


def test_export_post(url: str, rest_config: dict) -> None:
    if not url:
        print("Export URL is blank; skipping POST/PUT test.")
        return

    payload = {
        "source_system": "Modula WMS",
        "document_type": "REST_SETUP_TEST",
        "orders": [
            {
                "order_id": "SETUP-TEST",
                "lines": [
                    {
                        "item": "BRG-100",
                        "quantity": "1",
                    }
                ],
            }
        ],
    }

    data = json.dumps(payload).encode("utf-8")
    headers = build_headers(rest_config)
    headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url,
        data=data,
        method=rest_config.get("export_method", "POST").upper(),
        headers=headers,
    )

    timeout = int(rest_config.get("timeout_seconds", 30))

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(500).decode("utf-8", errors="replace")
            print(f"Export test succeeded. HTTP {response.status}")
            print(f"Response preview: {body}")
    except urllib.error.HTTPError as error:
        print(f"Export test failed. HTTP {error.code}: {error.reason}")
    except Exception as error:
        print(f"Export test failed: {error}")


def configure_rest_api(config: dict) -> dict:
    rest_config = dict(config.get("rest_api", {}) or {})

    print("=" * 70)
    print("REST API SETUP")
    print("=" * 70)
    print("This setup updates only config.json -> rest_api.")
    print("Leave optional values blank if the customer API does not need them.")
    print("=" * 70)

    import_enabled = ask_yes_no(
        "Enable REST API import? Customer API -> Modula",
        bool(rest_config.get("import_enabled", False)),
    )

    export_enabled = ask_yes_no(
        "Enable REST API export? Modula -> Customer API",
        bool(rest_config.get("export_enabled", False)),
    )

    rest_config["enabled"] = import_enabled or export_enabled
    rest_config["import_enabled"] = import_enabled
    rest_config["export_enabled"] = export_enabled

    if import_enabled:
        rest_config["import_url"] = ask_text(
            "Import GET URL",
            rest_config.get("import_url", ""),
        )
        rest_config["records_key"] = ask_text(
            "Records key/path in API response",
            rest_config.get("records_key", "orders"),
        )

    if export_enabled:
        rest_config["export_url"] = ask_text(
            "Export POST/PUT URL",
            rest_config.get("export_url", ""),
        )

        export_method = ask_text(
            "Export method",
            rest_config.get("export_method", "POST"),
        ).upper()

        if export_method not in ["POST", "PUT"]:
            print("Unsupported export method entered; defaulting to POST.")
            export_method = "POST"

        rest_config["export_method"] = export_method
        rest_config["batch_key"] = ask_text(
            "Export batch key",
            rest_config.get("batch_key", "orders"),
        )

    rest_config["headers"] = ask_json_object(
        "Optional request headers as JSON object",
        rest_config.get("headers", {}),
    )

    rest_config["params"] = ask_json_object(
        "Optional query params as JSON object",
        rest_config.get("params", {}),
    )

    rest_config["api_key"] = ask_text(
        "API key/token, optional",
        rest_config.get("api_key", ""),
    )

    if rest_config.get("api_key"):
        rest_config["api_key_header"] = ask_text(
            "API key header",
            rest_config.get("api_key_header", "Authorization"),
        )
        rest_config["bearer_token"] = ask_yes_no(
            "Use Bearer token format?",
            bool(rest_config.get("bearer_token", True)),
        )
    else:
        rest_config["api_key_header"] = rest_config.get(
            "api_key_header",
            "Authorization",
        )
        rest_config["bearer_token"] = bool(rest_config.get("bearer_token", True))

    rest_config["poll_interval_seconds"] = ask_int(
        "REST import poll interval in seconds",
        int(rest_config.get("poll_interval_seconds", 60)),
    )

    rest_config["timeout_seconds"] = ask_int(
        "Request timeout in seconds",
        int(rest_config.get("timeout_seconds", 30)),
    )

    rest_config["max_retries"] = ask_int(
        "Max request retries",
        int(rest_config.get("max_retries", 3)),
    )

    config["rest_api"] = rest_config
    return config


def main() -> None:
    config = load_config()
    config = configure_rest_api(config)
    save_config(config)

    print()
    print("REST API settings saved to config.json.")

    rest_config = config.get("rest_api", {})

    if rest_config.get("import_enabled") and ask_yes_no(
        "Test REST import GET now?",
        True,
    ):
        test_get(rest_config.get("import_url", ""), rest_config)

    if rest_config.get("export_enabled") and ask_yes_no(
        "Send a small test export POST/PUT now?",
        False,
    ):
        test_export_post(rest_config.get("export_url", ""), rest_config)

    print()
    print("Setup complete. You can now run start.bat or always_on_runtime.py.")


if __name__ == "__main__":
    main()
