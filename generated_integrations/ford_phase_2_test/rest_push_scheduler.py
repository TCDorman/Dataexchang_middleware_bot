"""
scheduler_runner.py

Generated scheduler scaffold for Ford Phase 2 Test.
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime


TARGET_SCRIPT = r"generated_integrations\ford_phase_2_test\rest_push_runner.py"
CONFIG_PATH = r"generated_integrations\ford_phase_2_test\rest_push_config.json"


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

    print(f"[{datetime.now().isoformat(timespec='seconds')}] Running: {' '.join(command)}")

    completed = subprocess.run(command)

    return completed.returncode


def run_forever(interval_minutes: int, dry_run: bool = False) -> None:
    while True:
        exit_code = run_once(dry_run=dry_run)

        print(
            f"[{datetime.now().isoformat(timespec='seconds')}] "
            f"Run finished with exit code {exit_code}. "
            f"Next run in {interval_minutes} minutes."
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
