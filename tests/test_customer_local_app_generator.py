"""
test_customer_local_app_generator.py
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.customer_local_app_generator import (
    generate_customer_local_app,
)

def main():
    result = generate_customer_local_app(
        customer_name="Ford",
        customer_profile_path="configs/customers/ford_profile.json",
        source_type="file",
    )

    print("CUSTOMER LOCAL APP GENERATION COMPLETE")
    print("=" * 60)
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()