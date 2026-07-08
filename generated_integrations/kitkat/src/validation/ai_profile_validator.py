"""
==================================================
AI Profile Validator
==================================================

Purpose:
    Validates AI-generated customer profiles before
    they are approved and saved.

Responsibilities:
    - Confirm required profile sections exist
    - Confirm required internal fields are mapped
    - Prevent invalid target fields
    - Detect duplicate target mappings
    - Validate confidence scores
    - Return a clear validation report
"""

# ==================================================
# Imports
# ==================================================

from typing import Dict, List


# ==================================================
# Constants
# ==================================================

REQUIRED_PROFILE_KEYS = [
    "customer_name",
    "header_signature",
    "field_mapping",
    "mapping_confidence",
    "mapping_notes",
]

REQUIRED_INTERNAL_FIELDS = [
    "order_id",
]

ALLOWED_INTERNAL_FIELDS = [
    "order_id",
    "customer_name",
    "item",
    "quantity",
]


# ==================================================
# AI Profile Validator
# ==================================================

class AIProfileValidator:
    """
    Validates AI-generated customer profiles.
    """

    def validate_profile(
        self,
        profile: Dict,
    ) -> Dict:
        """
        Validate an AI-generated customer profile.

        Args:
            profile:
                AI-generated profile dictionary.

        Returns:
            Validation result dictionary.
        """

        errors: List[str] = []
        warnings: List[str] = []

        self._validate_required_keys(profile, errors)
        self._validate_header_signature(profile, errors)
        self._validate_field_mapping(profile, errors, warnings)
        self._validate_confidence_scores(profile, errors, warnings)

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def _validate_required_keys(
        self,
        profile: Dict,
        errors: List[str],
    ) -> None:
        """
        Validate that all required profile keys exist.

        Args:
            profile:
                AI-generated profile dictionary.
            errors:
                List of validation errors.
        """

        for key in REQUIRED_PROFILE_KEYS:
            if key not in profile:
                errors.append(f"Missing required profile key: {key}")

    def _validate_header_signature(
        self,
        profile: Dict,
        errors: List[str],
    ) -> None:
        """
        Validate the header signature section.

        Args:
            profile:
                AI-generated profile dictionary.
            errors:
                List of validation errors.
        """

        header_signature = profile.get("header_signature")

        if not isinstance(header_signature, list):
            errors.append("header_signature must be a list.")
            return

        if not header_signature:
            errors.append("header_signature cannot be empty.")

    def _validate_field_mapping(
        self,
        profile: Dict,
        errors: List[str],
        warnings: List[str],
    ) -> None:
        """
        Validate field mapping structure and contents.

        Args:
            profile:
                AI-generated profile dictionary.
            errors:
                List of validation errors.
            warnings:
                List of validation warnings.
        """

        field_mapping = profile.get("field_mapping")

        if not isinstance(field_mapping, dict):
            errors.append("field_mapping must be a dictionary.")
            return

        if not field_mapping:
            errors.append("field_mapping cannot be empty.")
            return

        mapped_internal_fields = list(field_mapping.values())

        for source_field, target_field in field_mapping.items():
            if target_field not in ALLOWED_INTERNAL_FIELDS:
                errors.append(
                    f"Invalid target field '{target_field}' "
                    f"mapped from source field '{source_field}'."
                )

        for required_field in REQUIRED_INTERNAL_FIELDS:
            if required_field not in mapped_internal_fields:
                errors.append(
                    f"Missing required internal field mapping: "
                    f"{required_field}"
                )

        duplicate_targets = self._find_duplicates(mapped_internal_fields)

        for duplicate in duplicate_targets:
            warnings.append(
                f"Duplicate target mapping detected: {duplicate}"
            )

    def _validate_confidence_scores(
        self,
        profile: Dict,
        errors: List[str],
        warnings: List[str],
    ) -> None:
        """
        Validate mapping confidence scores.

        Args:
            profile:
                AI-generated profile dictionary.
            errors:
                List of validation errors.
            warnings:
                List of validation warnings.
        """

        field_mapping = profile.get("field_mapping", {})
        mapping_confidence = profile.get("mapping_confidence")

        if not isinstance(mapping_confidence, dict):
            errors.append("mapping_confidence must be a dictionary.")
            return

        for source_field in field_mapping:
            if source_field not in mapping_confidence:
                warnings.append(
                    f"Missing confidence score for source field: "
                    f"{source_field}"
                )
                continue

            score = mapping_confidence[source_field]

            if not isinstance(score, int):
                errors.append(
                    f"Confidence score for '{source_field}' "
                    "must be an integer."
                )
                continue

            if score < 0 or score > 100:
                errors.append(
                    f"Confidence score for '{source_field}' "
                    "must be between 0 and 100."
                )

            if score < 80:
                warnings.append(
                    f"Low confidence mapping for '{source_field}': "
                    f"{score}%"
                )

    def _find_duplicates(
        self,
        values: List[str],
    ) -> List[str]:
        """
        Find duplicate values in a list.

        Args:
            values:
                List of values to inspect.

        Returns:
            List of duplicate values.
        """

        seen = set()
        duplicates = set()

        for value in values:
            if value in seen:
                duplicates.add(value)

            seen.add(value)

        return list(duplicates)