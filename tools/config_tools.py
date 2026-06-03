import json
from pathlib import Path


DEFAULT_CONFIG_PATH = "configs/app/local_settings.json"


def load_local_settings(config_path: str = DEFAULT_CONFIG_PATH):
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Local settings file not found: {config_path}")

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_setting(key: str, config_path: str = DEFAULT_CONFIG_PATH):
    settings = load_local_settings(config_path)

    if key not in settings:
        raise KeyError(f"Setting not found: {key}")

    return settings[key]