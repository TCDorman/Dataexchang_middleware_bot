"""
test_package_recommendation_agent.py

Tests requirements analysis, blueprint generation, and package recommendation.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.auto_integration_workflow import AutoIntegrationWorkflow
from agents.package_recommendation_agent import PackageRecommendationAgent


def main():
    requirements = """
Customer: Ford

ERP System:
SAP

Requirements:
- Orders are exported nightly as CSV files from SAP.
- Modula WMS must import those orders.
- Inventory transactions must be sent back to SAP through REST API.
- Serialized products require serial number tracking.
- Item master data should synchronize every 4 hours.
- Failed integrations must be logged and retried automatically.
"""

    auto_workflow = AutoIntegrationWorkflow()
    recommendation_agent = PackageRecommendationAgent()

    auto_result = auto_workflow.run_from_requirements(
        requirements_text=requirements,
    )

    blueprint = auto_result["blueprint"]

    recommendation = recommendation_agent.recommend_packages(
        blueprint=blueprint,
    )

    print("=" * 70)
    print("AUTO WORKFLOW RESULT")
    print("=" * 70)
    print(json.dumps(auto_result, indent=4))

    print("\n" + "=" * 70)
    print("PACKAGE RECOMMENDATION")
    print("=" * 70)
    print(json.dumps(recommendation, indent=4))

    if recommendation.get("status") != "success":
        raise RuntimeError("Package recommendation failed.")

    if not recommendation.get("recommended_packages"):
        raise RuntimeError("No package recommendations were produced.")

    print("\n✅ PACKAGE RECOMMENDATION TEST PASSED")


if __name__ == "__main__":
    main()