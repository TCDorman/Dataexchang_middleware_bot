"""
openai_profile_review_agent.py

Reviews a generated customer integration profile and produces:
- readiness score
- risk level
- missing fields
- warnings
- recommendations
"""

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()


REQUIRED_FIELDS = [
    "order_id",
    "item",
    "quantity",
]


OPTIONAL_BUT_IMPORTANT_FIELDS = [
    "customer_name",
    "ship_to_name",
    "ship_to_address",
    "location",
]


def review_customer_profile(profile_path: str) -> dict[str, Any]:
    path = Path(profile_path)

    if not path.exists():
        return {
            "status": "error",
            "message": f"Profile not found: {profile_path}",
        }

    with open(path, "r", encoding="utf-8") as file:
        profile = json.load(file)

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return _fallback_review(
            profile=profile,
            profile_path=str(path),
            reason="OPENAI_API_KEY is not set.",
        )

    try:
        from openai import OpenAI
    except ImportError:
        return _fallback_review(
            profile=profile,
            profile_path=str(path),
            reason="openai package is not installed. Run: pip install openai",
        )

    client = OpenAI(api_key=api_key)

    prompt = {
        "task": "Review a Modula WMS customer integration profile.",
        "profile": profile,
        "required_fields": REQUIRED_FIELDS,
        "optional_but_important_fields": OPTIONAL_BUT_IMPORTANT_FIELDS,
        "requirements": {
            "return_json_only": True,
            "integration_readiness_score_0_to_100": True,
            "risk_level_values": ["low", "medium", "high"],
            "include_missing_fields": True,
            "include_warnings": True,
            "include_recommendations": True,
        },
        "expected_json_shape": {
            "status": "success",
            "review_method": "openai",
            "integration_readiness_score": 0,
            "risk_level": "low | medium | high",
            "missing_required_fields": [],
            "missing_optional_fields": [],
            "warnings": [],
            "recommendations": [],
            "summary": "short review summary",
        },
    }

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert WMS/ERP integration reviewer. "
                        "Return only valid JSON. Do not include markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(prompt, indent=2),
                },
            ],
            temperature=0,
        )

        content = response.choices[0].message.content
        parsed = json.loads(content)

        parsed["profile_path"] = str(path)

        output_path = (
            Path("generated_integrations")
            / "profile_reviews"
            / f"{path.stem}_review.json"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(parsed, file, indent=4)

        parsed["output_path"] = str(output_path)

        return parsed

    except Exception as error:
        return _fallback_review(
            profile=profile,
            profile_path=str(path),
            reason=f"OpenAI profile review failed: {error}",
        )


def _fallback_review(
    profile: dict,
    profile_path: str,
    reason: str,
) -> dict[str, Any]:
    field_mapping = profile.get("field_mapping", {})

    missing_required = [
        field for field in REQUIRED_FIELDS
        if not field_mapping.get(field)
    ]

    missing_optional = [
        field for field in OPTIONAL_BUT_IMPORTANT_FIELDS
        if not field_mapping.get(field)
    ]

    score = 100
    score -= len(missing_required) * 25
    score -= len(missing_optional) * 5
    score = max(score, 0)

    if missing_required:
        risk_level = "high"
    elif score < 85:
        risk_level = "medium"
    else:
        risk_level = "low"

    review = {
        "status": "success",
        "review_method": "fallback_rule_based",
        "fallback_reason": reason,
        "profile_path": profile_path,
        "integration_readiness_score": score,
        "risk_level": risk_level,
        "missing_required_fields": missing_required,
        "missing_optional_fields": missing_optional,
        "warnings": _build_warnings(missing_required, missing_optional),
        "recommendations": _build_recommendations(
            missing_required,
            missing_optional,
        ),
        "summary": (
            f"Profile review completed using fallback rules. "
            f"Risk level is {risk_level} with readiness score {score}."
        ),
    }

    output_path = (
        Path("generated_integrations")
        / "profile_reviews"
        / f"{Path(profile_path).stem}_review.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(review, file, indent=4)

    review["output_path"] = str(output_path)

    return review


def _build_warnings(
    missing_required: list[str],
    missing_optional: list[str],
) -> list[str]:
    warnings = []

    for field in missing_required:
        warnings.append(
            f"Required field '{field}' is missing and may block XML generation."
        )

    for field in missing_optional:
        warnings.append(
            f"Optional field '{field}' is missing; integration may still run."
        )

    return warnings


def _build_recommendations(
    missing_required: list[str],
    missing_optional: list[str],
) -> list[str]:
    recommendations = []

    for field in missing_required:
        recommendations.append(
            f"Ask customer to provide or identify a source column for '{field}'."
        )

    for field in missing_optional:
        recommendations.append(
            f"Consider requesting '{field}' for richer Modula order data."
        )

    if not recommendations:
        recommendations.append(
            "Profile appears ready for standard Modula XML generation."
        )

    return recommendations