"""
setup_rest_api.py

Simple customer REST API setup utility.

Run from the generated package folder:
    python setup_rest_api.py

Or double-click:
    setup_api.bat

The customer only needs to provide:
1. REST import endpoint
2. REST export endpoint

All other REST API settings use the existing/default configuration.
"""

import json
from pathlib import Path


# ============================================================
# Paths
# ============================================================

PACKAGE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = PACKAGE_DIR / "config.json"


# ============================================================
# Config Helpers
# ============================================================

def load_config() -> dict:
    """
    Load the generated package config.json.
    """

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Missing config.json: {CONFIG_PATH}"
        )

    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def save_config(config: dict) -> None:
    """
    Save config.json.
    """

    with open(CONFIG_PATH, "w", encoding="utf-8") as file:
        json.dump(
            config,
            file,
            indent=4,
        )


# ============================================================
# Input Helper
# ============================================================

def ask_endpoint(
    prompt: str,
    current_value: str = "",
) -> str:
    """
    Ask for an API endpoint.

    If an endpoint already exists in config.json,
    display it as the default.
    """

    current_value = str(current_value or "").strip()

    if current_value:
        value = input(
            f"{prompt} [{current_value}]: "
        ).strip()

        return value or current_value

    return input(
        f"{prompt}: "
    ).strip()


# ============================================================
# REST Configuration
# ============================================================

def configure_rest_api(config: dict) -> dict:
    """
    Configure only the REST import and export endpoints.

    All advanced REST settings remain unchanged or use
    safe runtime defaults.
    """

    rest_config = dict(
        config.get("rest_api", {}) or {}
    )

    print()
    print("=" * 60)
    print("MODULA REST API SETUP")
    print("=" * 60)
    print()
    print(
        "Enter the customer REST API endpoints used by "
        "the middleware."
    )
    print()

    # --------------------------------------------------------
    # Import endpoint
    # --------------------------------------------------------

    import_url = ask_endpoint(
        "Import endpoint  (Customer -> Modula)",
        rest_config.get("import_url", ""),
    )

    # --------------------------------------------------------
    # Export endpoint
    # --------------------------------------------------------

    export_url = ask_endpoint(
        "Export endpoint  (Modula -> Customer)",
        rest_config.get("export_url", ""),
    )

    # --------------------------------------------------------
    # Save endpoint configuration
    # --------------------------------------------------------

    rest_config["import_url"] = import_url
    rest_config["export_url"] = export_url

    # Automatically enable each direction when an endpoint exists.
    rest_config["import_enabled"] = bool(import_url)
    rest_config["export_enabled"] = bool(export_url)

    rest_config["enabled"] = (
        rest_config["import_enabled"]
        or rest_config["export_enabled"]
    )

    # --------------------------------------------------------
    # Runtime defaults
    #
    # These are not shown to the customer.
    # Existing configured values are preserved.
    # --------------------------------------------------------

    rest_config.setdefault(
        "records_key",
        "",
    )

    rest_config.setdefault(
        "export_method",
        "POST",
    )

    rest_config.setdefault(
        "batch_key",
        "orders",
    )

    rest_config.setdefault(
        "headers",
        {},
    )

    rest_config.setdefault(
        "params",
        {},
    )

    rest_config.setdefault(
        "api_key",
        "",
    )

    rest_config.setdefault(
        "api_key_header",
        "Authorization",
    )

    rest_config.setdefault(
        "bearer_token",
        True,
    )

    rest_config.setdefault(
        "poll_interval_seconds",
        60,
    )

    rest_config.setdefault(
        "timeout_seconds",
        30,
    )

    rest_config.setdefault(
        "max_retries",
        3,
    )

    config["rest_api"] = rest_config

    return config


# ============================================================
# Main
# ============================================================

def main() -> None:
    """
    Run REST API setup.
    """

    try:
        config = load_config()

        config = configure_rest_api(config)

        save_config(config)

        rest_config = config["rest_api"]

        print()
        print("=" * 60)
        print("REST API SETUP COMPLETE")
        print("=" * 60)
        print()

        if rest_config.get("import_url"):
            print(
                "Import endpoint:"
            )
            print(
                f"  {rest_config['import_url']}"
            )
        else:
            print(
                "Import endpoint: Not configured"
            )

        print()

        if rest_config.get("export_url"):
            print(
                "Export endpoint:"
            )
            print(
                f"  {rest_config['export_url']}"
            )
        else:
            print(
                "Export endpoint: Not configured"
            )

        print()
        print(
            "Configuration saved to config.json."
        )
        print()
        print(
            "The middleware is ready to use these "
            "REST API endpoints."
        )
        print()

    except Exception as error:
        print()
        print("=" * 60)
        print("REST API SETUP FAILED")
        print("=" * 60)
        print()
        print(error)
        print()


if __name__ == "__main__":
    main()