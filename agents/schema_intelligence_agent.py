import sys
import re
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parents[1])
)

import pandas as pd

from agents.dynamic_mapping_agent import (
    infer_mapping_from_columns,
)

# ==================================================
# Value Pattern Checks
# ==================================================
def looks_numeric(values):
    """
    Check whether most sample values look numeric.

    Useful for detecting quantity fields.
    """
    checked_values = [
        value
        for value in values
        if str(value).strip()
        and str(value).lower() != "nan"
    ]

    if not checked_values:
        return 0

    numeric_count = 0

    for value in checked_values:
        try:
            float(value)
            numeric_count += 1
        except ValueError:
            pass

    return numeric_count / len(checked_values)


def looks_like_item_code(values):
    """
    Check whether values look like item/SKU/part codes.

    Examples:
    ABC123
    PART-001
    SKU_9988
    """
    checked_values = [
        str(value).strip()
        for value in values
        if str(value).strip()
        and str(value).lower() != "nan"
    ]

    if not checked_values:
        return 0

    item_like_count = 0

    for value in checked_values:
        has_letter = bool(re.search(r"[A-Za-z]", value))
        has_number = bool(re.search(r"\d", value))

        if has_letter and has_number:
            item_like_count += 1

    return item_like_count / len(checked_values)


def looks_like_name(values):
    """
    Check whether values look like customer/company names.

    This is intentionally simple for now:
    - mostly text
    - not mostly numeric
    - not item-code-like
    """
    checked_values = [
        str(value).strip()
        for value in values
        if str(value).strip()
        and str(value).lower() != "nan"
    ]

    if not checked_values:
        return 0

    name_like_count = 0

    for value in checked_values:
        has_letter = bool(re.search(r"[A-Za-z]", value))
        has_number = bool(re.search(r"\d", value))

        if has_letter and not has_number:
            name_like_count += 1

    return name_like_count / len(checked_values)


# ==================================================
# Analyze One Column
# ==================================================
def analyze_column_values(series):
    """
    Analyze sample values from a single column and return
    evidence scores for possible canonical fields.
    """
    sample_values = series.dropna().head(10).tolist()

    numeric_score = looks_numeric(sample_values)
    item_score = looks_like_item_code(sample_values)
    name_score = looks_like_name(sample_values)

    return {
        "quantity": int(numeric_score * 80),
        "item": int(item_score * 80),
        "customer_name": int(name_score * 70),
    }


# ==================================================
# Combine Header + Value Intelligence
# ==================================================
def infer_mapping_with_samples(file_path: str):
    """
    Infer field mappings using both:
    1. Column/header names
    2. Sample value patterns

    This improves mapping when headers are vague, such as:
    ID, NAME, CODE, AMOUNT
    """
    df = pd.read_csv(file_path)

    header_result = infer_mapping_from_columns(df.columns)

    header_mapping = header_result["mapping"]
    header_confidence = header_result["confidence"]

    field_scores = {
        "order_id": {},
        "customer_name": {},
        "item": {},
        "quantity": {},
        "operation_type": {},
    }

    # ----------------------------------------------
    # Add header-based scores
    # ----------------------------------------------
    for canonical_field, column_name in header_mapping.items():
        if column_name:
            field_scores[canonical_field][column_name] = (
                header_confidence.get(canonical_field, 0)
            )

    # ----------------------------------------------
    # Add value-pattern scores
    # ----------------------------------------------
    for column in df.columns:
        value_scores = analyze_column_values(df[column])

        for canonical_field, score in value_scores.items():
            existing_score = field_scores[canonical_field].get(
                column,
                0,
            )

            field_scores[canonical_field][column] = max(
                existing_score,
                score,
            )

    # ----------------------------------------------
    # Pick best column for each canonical field
    # ----------------------------------------------
    final_mapping = {}
    final_confidence = {}

    used_columns = set()

    for canonical_field, scores in field_scores.items():
        best_column = None
        best_score = 0

        for column, score in scores.items():
            if column in used_columns:
                continue

            if score > best_score:
                best_column = column
                best_score = score

        final_mapping[canonical_field] = best_column
        final_confidence[canonical_field] = best_score

        if best_column:
            used_columns.add(best_column)

    return {
        "file_path": file_path,
        "columns": list(df.columns),
        "mapping": final_mapping,
        "confidence": final_confidence,
        "sample_rows": df.head(3).to_dict(orient="records"),
    }


# ==================================================
# Analyze Multiple Files
# ==================================================
def analyze_files_with_schema_intelligence(file_paths: list[str]):
    """
    Analyze one or more CSV files using schema intelligence.
    """
    results = []

    for file_path in file_paths:
        extension = Path(file_path).suffix.lower()

        if extension != ".csv":
            results.append(
                {
                    "file_path": file_path,
                    "error": f"Unsupported file type: {extension}",
                }
            )
            continue

        results.append(
            infer_mapping_with_samples(file_path)
        )

    return results


# ==================================================
# Manual Test
# ==================================================
if __name__ == "__main__":
    results = analyze_files_with_schema_intelligence(
        [
            "data/customer_input/ford_test_headers.csv",
            "data/customer_input/ford_test_lines.csv",
        ]
    )

    for result in results:
        print("\nFile:")
        print(result["file_path"])

        print("\nColumns:")
        print(result["columns"])

        print("\nMapping:")
        print(result["mapping"])

        print("\nConfidence:")
        print(result["confidence"])

        print("\nSample Rows:")
        print(result["sample_rows"])