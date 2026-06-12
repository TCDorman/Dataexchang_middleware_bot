"""
dashboard_agent.py

Builds a dashboard summary of all registered customer profiles.
"""

from pathlib import Path
from typing import Any

from agents.openai_profile_review_agent import review_customer_profile


def build_integration_dashboard(
    profiles_dir: str = "configs/customers",
) -> dict[str, Any]:
    profiles_path = Path(profiles_dir)

    if not profiles_path.exists():
        return {
            "status": "error",
            "message": f"Profiles directory not found: {profiles_dir}",
            "customers": [],
        }

    customers = []

    for profile_file in profiles_path.glob("*.json"):
        review = review_customer_profile(str(profile_file))

        customers.append(
            {
                "customer_name": _get_customer_name(profile_file, review),
                "profile_path": str(profile_file),
                "score": review.get("integration_readiness_score"),
                "risk": review.get("risk_level"),
                "review_method": review.get("review_method"),
                "review_output_path": review.get("output_path"),
                "missing_required_fields": review.get(
                    "missing_required_fields",
                    [],
                ),
                "missing_optional_fields": review.get(
                    "missing_optional_fields",
                    [],
                ),
                "recommendations": review.get("recommendations", []),
            }
        )

    customers.sort(
        key=lambda customer: customer.get("score") or 0,
        reverse=True,
    )

    return {
        "status": "success",
        "profiles_dir": str(profiles_path),
        "customers_reviewed": len(customers),
        "customers": customers,
    }


def _get_customer_name(profile_file: Path, review: dict) -> str:
    try:
        import json

        with open(profile_file, "r", encoding="utf-8") as file:
            profile = json.load(file)

        return profile.get("customer_name") or profile_file.stem

    except Exception:
        return profile_file.stem