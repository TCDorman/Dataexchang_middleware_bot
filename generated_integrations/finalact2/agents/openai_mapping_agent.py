import json
import os

from openai import OpenAI


# ==================================================
# OpenAI Client
# ==================================================
def get_openai_client():
    """
    Create an OpenAI client using OPENAI_API_KEY from
    the environment.
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError(
            "OPENAI_API_KEY environment variable is not set."
        )

    return OpenAI()


# ==================================================
# Infer Mapping With OpenAI
# ==================================================
def infer_mapping_with_openai(
    columns: list,
    sample_rows: list,
):
    """
    Ask OpenAI to map customer fields to Modula canonical fields.

    Expected output:
    {
        "order_id": "PO_NUM",
        "customer_name": "BUYER",
        "item": "PART_NO",
        "quantity": "QTY_REQ",
        "operation_type": null
    }
    """
    client = get_openai_client()

    prompt = {
        "task": "Map customer ERP fields to Modula WMS canonical fields.",
        "canonical_fields": [
            "order_id",
            "customer_name",
            "item",
            "quantity",
            "operation_type",
        ],
        "columns": columns,
        "sample_rows": sample_rows,
        "rules": [
            "Return only valid JSON.",
            "Use null when no matching source column exists.",
            "Do not invent source columns.",
        ],
    }

    response = client.responses.create(
        model="gpt-5.5-mini",
        input=(
            "You are a data integration mapping assistant. "
            "Return only a JSON object.\n\n"
            + json.dumps(prompt, indent=2)
        ),
    )

    return json.loads(response.output_text)