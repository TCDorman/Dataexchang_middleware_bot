"""
test_requirements_analysis_agent.py
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ai.requirements_analysis_agent import (
    RequirementsAnalysisAgent,
)


def main():
    requirements = """
Customer: Ford

ERP System:
SAP

Requirements:

- Orders are exported nightly as CSV files.
- Modula WMS must import those orders.
- Inventory transactions must be sent back to SAP.
- Inventory transactions should use a REST API.
- Serialized products require serial number tracking.
- Item master data should synchronize every 4 hours.
- Failed integrations must be logged and retried automatically.
"""

    agent = RequirementsAnalysisAgent()

    result = agent.analyze_requirements(
        requirements_text=requirements,
    )

    print("=" * 70)
    print("REQUIREMENTS ANALYSIS RESULT")
    print("=" * 70)
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()