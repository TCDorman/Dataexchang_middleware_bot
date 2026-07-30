"""
scheduler_scaffold_generator.py

Generates a simple scheduler wrapper for REST integration scripts.
"""

from pathlib import Path


class SchedulerScaffoldGenerator:
    """
    Generates a scheduler script that can repeatedly run a pull or push runner.
    """

    def generate(
        self,
        customer_name: str,
        output_folder: str,
        target_script: str,
        config_path: str,
        script_name: str = "scheduler_runner.py",
    ) -> dict:
        output_path = Path(output_folder) / script_name
        output_path.parent.mkdir(parents=True, exist_ok=True)

        script_content = self._build_script(
            customer_name=customer_name,
            target_script=target_script,
            config_path=config_path,
        )

        with open(output_path, "w", encoding="utf-8") as file:
            file.write(script_content)

        return {
            "status": "success",
            "customer_name": customer_name,
            "script_path": str(output_path),
        }

    def _build_script(
        self,
        customer_name: str,
        target_script: str,
        config_path: str,
    ) -> str:
        return f'''"""
scheduler_runner.py

Generated scheduler scaffold for {customer_name}.
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime


TARGET_SCRIPT = r"{target_script}"
CONFIG_PATH = r"{config_path}"


def run_once(dry_run: bool = False) -> int:
    command = [
        sys.executable,
        TARGET_SCRIPT,
        "--config",
        CONFIG_PATH,
        "--once",
    ]

    if dry_run:
        command.append("--dry-run")

    print(f"[{{datetime.now().isoformat(timespec='seconds')}}] Running: {{' '.join(command)}}")

    completed = subprocess.run(command)

    return completed.returncode


def run_forever(interval_minutes: int, dry_run: bool = False) -> None:
    while True:
        exit_code = run_once(dry_run=dry_run)

        print(
            f"[{{datetime.now().isoformat(timespec='seconds')}}] "
            f"Run finished with exit code {{exit_code}}. "
            f"Next run in {{interval_minutes}} minutes."
        )

        time.sleep(interval_minutes * 60)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--interval-minutes", type=int, default=15)

    args = parser.parse_args()

    if args.once:
        exit_code = run_once(dry_run=args.dry_run)
        raise SystemExit(exit_code)

    run_forever(
        interval_minutes=args.interval_minutes,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
'''