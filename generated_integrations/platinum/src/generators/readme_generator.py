"""
readme_generator.py

Generates a README.md file for generated customer integration packages.
"""

from datetime import datetime
from pathlib import Path


class ReadmeGenerator:
    """
    Generates a README.md describing a generated integration package.
    """

    def generate(
        self,
        customer_name: str,
        output_folder: str,
        source_type: str = "rest_api",
        filename: str = "README.md",
    ) -> dict:
        output_path = Path(output_folder) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        content = self._build_readme(
            customer_name=customer_name,
            source_type=source_type,
        )

        with open(output_path, "w", encoding="utf-8") as file:
            file.write(content)

        return {
            "status": "success",
            "readme_path": str(output_path),
        }

    def _build_readme(
        self,
        customer_name: str,
        source_type: str,
    ) -> str:
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return f"""
# {customer_name} Integration Package

## Overview

This package was generated automatically by the Modula WMS Data Integration Agent.

- Customer: {customer_name}
- Source Type: {source_type}
- Generated: {generated_at}

## Included Files

- rest_pull_runner.py — Pulls data from a REST API.
- rest_push_runner.py — Pushes data to a REST API.
- rest_pull_config.json — Configuration for REST pull.
- rest_push_config.json — Configuration for REST push.
- rest_pull_scheduler.py — Scheduler wrapper for pull operations.
- rest_push_scheduler.py — Scheduler wrapper for push operations.
- logs/ — Stores runtime logs.
- data/dead_letter/ — Stores failed push records.

## Typical Commands

Run a one-time pull:

    python rest_pull_runner.py --config rest_pull_config.json --once

Run a pull dry-run:

    python rest_pull_runner.py --config rest_pull_config.json --once --dry-run

Run a one-time push:

    python rest_push_runner.py --config rest_push_config.json --once

Run a push dry-run:

    python rest_push_runner.py --config rest_push_config.json --once --dry-run

Run scheduled polling every 15 minutes:

    python rest_pull_scheduler.py --interval-minutes 15

Run scheduled pushing every 15 minutes:

    python rest_push_scheduler.py --interval-minutes 15

## Logging

Runner logs are written to the logs/ directory.

## Dead Letter Queue

Failed push records are written to data/dead_letter/ for later review.

## Deployment Notes

1. Review both config files before running live.
2. Confirm endpoint URLs are correct.
3. Confirm authentication settings are correct.
4. Confirm field mappings are correct.
5. Run with --dry-run first.
6. Run without --dry-run only after validation is complete.
"""