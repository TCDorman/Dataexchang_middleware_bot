
# Ford Auto REST Integration Package

## Overview

This package was generated automatically by the Modula WMS Data Integration Agent.

- Customer: Ford Auto REST
- Source Type: rest_api
- Generated: 2026-06-23 11:44:22

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
