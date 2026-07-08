"""
==================================================
Schema Intelligence Agent
==================================================

Purpose:
    Infers field mappings from customer CSV files using:
    - OpenAI mapping when available
    - fallback header/value pattern intelligence

Responsibilities:
    - Read CSV files
    - Analyze column names
    - Analyze sample values
    - Return suggested mappings and confidence scores
"""

# ==================================================
# Imports
# ==================================================

import sys
import re
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parents[1])
)

import pandas as pd

from agents.openai_mapping_agent import infer_mapping_with_openai
from agents.dynamic_mapping_agent import infer_mapping_from_columns


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
# OpenAI Mapping Attempt
# ==================================================

def try_openai_mapping(
    file_path: str,
    df: pd.DataFrame,
):
    """
    Try to infer mapping using OpenAI.

    Args:
        file_path:
            CSV file path.
        df:
            Loaded CSV dataframe.

    Returns:
        OpenAI mapping result if successful, otherwise None.
    """

    try:
        sample_record = {
            "columns": list(df.columns),
            "sample_rows": df.head(5).to_dict(
                orient="records"
            ),
        }

        openai_mapping = infer_mapping_with_openai(
            sample_record
        )

        if not isinstance(openai_mapping, dict):
            return None

        if "error" in openai_mapping:
            return None

        return {
            "file_path": file_path,
            "columns": list(df.columns),
            "mapping": openai_mapping,
            "confidence": {
                field: 95 if column else 0
                for field, column in openai_mapping.items()
            },
            "sample_rows": df.head(3).to_dict(
                orient="records"
            ),
            "mapping_source": "openai",
        }

    except Exception as error:
        print(
            f"OpenAI mapping unavailable, using fallback: {error}"
        )

        return None


# ==================================================
# Fallback Mapping
# ==================================================

def infer_mapping_with_fallback(
    file_path: str,
    df: pd.DataFrame,
):
    """
    Infer field mappings using header names and value patterns.
    """

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

    for canonical_field, column_name in header_mapping.items():
        if column_name:
            field_scores[canonical_field][column_name] = (
                header_confidence.get(canonical_field, 0)
            )

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
        "sample_rows": df.head(3).to_dict(
            orient="records"
        ),
        "mapping_source": "fallback",
    }


# ==================================================
# Combine Header + Value Intelligence
# ==================================================

def infer_mapping_with_samples(file_path: str):
    """
    Infer field mappings using:
    1. OpenAI, if available
    2. Fallback header/value intelligence
    """

    df = pd.read_csv(file_path)

    openai_result = try_openai_mapping(
        file_path=file_path,
        df=df,
    )

    if openai_result:
        return openai_result

    return infer_mapping_with_fallback(
        file_path=file_path,
        df=df,
    )


# ==================================================
# Analyze Multiple Files
# ==================================================

def analyze_files_with_schema_intelligence(
    file_paths: list[str],
):
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