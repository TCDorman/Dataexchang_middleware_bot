"""
rest_config_generator.py

Generates JSON config files for REST pull and push runners.
"""

import json
from pathlib import Path
from typing import Any


class RestConfigGenerator:
    """
    Generates REST integration config files.
    """

    def generate_pull_config(
        self,
        output_folder: str,
        url: str,
        config_name: str = "rest_pull_config.json",
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        api_key: str | None = None,
        api_key_header: str = "Authorization",
        bearer_token: bool = True,
        output_data_folder: str = "data/rest_pull_output",
        log_path: str = "logs/rest_pull_runner.log",
    ) -> dict:
        output_path = Path(output_folder) / config_name
        output_path.parent.mkdir(parents=True, exist_ok=True)

        config = {
            "url": url,
            "params": params or {},
            "headers": headers or {},
            "api_key": api_key,
            "api_key_header": api_key_header,
            "bearer_token": bearer_token,
            "timeout": 30,
            "output_folder": output_data_folder,
            "log_path": log_path,
        }

        self._write_json(output_path, config)

        return {
            "status": "success",
            "config_type": "rest_pull",
            "config_path": str(output_path),
        }

    def generate_push_config(
        self,
        output_folder: str,
        url: str,
        source_path: str,
        field_mapping: dict[str, str],
        config_name: str = "rest_push_config.json",
        method: str = "POST",
        headers: dict[str, str] | None = None,
        api_key: str | None = None,
        api_key_header: str = "Authorization",
        bearer_token: bool = True,
        log_path: str = "logs/rest_push_runner.log",
        dead_letter_folder: str = "data/dead_letter",
    ) -> dict:
        output_path = Path(output_folder) / config_name
        output_path.parent.mkdir(parents=True, exist_ok=True)

        config = {
            "url": url,
            "source_path": source_path,
            "field_mapping": field_mapping,
            "method": method.upper(),
            "headers": headers or {},
            "api_key": api_key,
            "api_key_header": api_key_header,
            "bearer_token": bearer_token,
            "timeout": 30,
            "log_path": log_path,
            "dead_letter_folder": dead_letter_folder,
        }

        self._write_json(output_path, config)

        return {
            "status": "success",
            "config_type": "rest_push",
            "config_path": str(output_path),
        }

    def _write_json(
        self,
        output_path: Path,
        data: dict,
    ) -> None:
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)