from pathlib import Path
import pandas as pd


# ==================================================
# Canonical WMS Fields
# ==================================================
CANONICAL_FIELDS = {
    "order_id": [
        "order_id",
        "order_number",
        "ord_ordine",
        "po_num",
        "po_number",
        "purchase_order",
        "sales_order",
        "sales_order_id",
        "client_order_ref",
    ],
    "customer_name": [
        "customer_name",
        "customer",
        "buyer",
        "company",
        "company_name",
        "client",
        "account",
        "ord_des",
    ],
    "item": [
        "item",
        "sku",
        "item_code",
        "part_no",
        "part_number",
        "product",
        "product_code",
        "product_sku",
        "material",
        "material_code",
        "rig_articolo",
    ],
    "quantity": [
        "quantity",
        "qty",
        "order_qty",
        "ordered_qty",
        "requested_quantity",
        "qty_requested",
        "qty_req",
        "amount",
        "rig_qtar",
    ],
    "operation_type": [
        "operation_type",
        "order_type",
        "process_type",
        "fulfillment_mode",
        "ord_tipoop",
    ],
}


# ==================================================
# Normalize Column Names
# ==================================================
def normalize_column_name(column_name: str):
    """
    Normalize column names so different formats can be
    compared more easily.

    Example:
    "PO Number" -> "po_number"
    "Part-No"   -> "part_no"
    """
    return (
        str(column_name)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace(".", "_")
    )


# ==================================================
# Score Column Match
# ==================================================
def score_column_match(column_name: str, possible_names: list[str]):
    """
    Score how closely a source column matches a canonical field.

    Higher score means stronger confidence.
    """
    normalized_column = normalize_column_name(column_name)

    for possible_name in possible_names:
        normalized_possible = normalize_column_name(possible_name)

        # Exact match is strongest.
        if normalized_column == normalized_possible:
            return 100

        # Partial match is useful for names like customer_name_text.
        if normalized_possible in normalized_column:
            return 75

        if normalized_column in normalized_possible:
            return 60

    return 0


# ==================================================
# Infer Mapping From Columns
# ==================================================
def infer_mapping_from_columns(columns):
    """
    Infer a mapping from incoming customer columns to
    canonical WMS fields.

    Returns:
    {
        "order_id": "PO_NUM",
        "customer_name": "BUYER",
        "item": "PART_NO",
        "quantity": "QTY_REQ"
    }
    """
    mapping = {}
    confidence = {}

    for canonical_field, possible_names in CANONICAL_FIELDS.items():
        best_column = None
        best_score = 0

        for column in columns:
            score = score_column_match(
                column,
                possible_names,
            )

            if score > best_score:
                best_column = column
                best_score = score

        if best_column and best_score > 0:
            mapping[canonical_field] = best_column
            confidence[canonical_field] = best_score
        else:
            mapping[canonical_field] = None
            confidence[canonical_field] = 0

    return {
        "mapping": mapping,
        "confidence": confidence,
    }


# ==================================================
# Analyze CSV File
# ==================================================
def analyze_csv_file(file_path: str):
    """
    Read a CSV file and infer its field mapping.
    """
    df = pd.read_csv(file_path)

    result = infer_mapping_from_columns(df.columns)

    return {
        "file_path": file_path,
        "columns": list(df.columns),
        "mapping": result["mapping"],
        "confidence": result["confidence"],
        "sample_rows": df.head(3).to_dict(orient="records"),
    }


# ==================================================
# Analyze Customer Files
# ==================================================
def analyze_customer_files(file_paths: list[str]):
    """
    Analyze one or more customer files and return inferred
    mappings for each file.
    """
    analyses = []

    for file_path in file_paths:
        extension = Path(file_path).suffix.lower()

        if extension == ".csv":
            analyses.append(
                analyze_csv_file(file_path)
            )
        else:
            analyses.append(
                {
                    "file_path": file_path,
                    "error": f"Unsupported file type: {extension}",
                }
            )

    return analyses


# ==================================================
# Manual Test
# ==================================================
if __name__ == "__main__":
    result = analyze_customer_files(
        [
            "data/customer_input/ford_test_headers.csv",
            "data/customer_input/ford_test_lines.csv",
        ]
    )

    for analysis in result:
        print("\nFile:")
        print(analysis["file_path"])

        print("\nColumns:")
        print(analysis.get("columns"))

        print("\nMapping:")
        print(analysis.get("mapping"))

        print("\nConfidence:")
        print(analysis.get("confidence"))