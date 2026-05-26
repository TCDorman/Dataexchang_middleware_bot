import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models.wms_models import WMSItem


def parse_customer_inventory_csv(file_path: str):
    df = pd.read_csv(file_path)

    items = []

    for _, row in df.iterrows():
        item = WMSItem(
            item_code=row["sku"],
            description=row["description"]
        )

        items.append(item)

    return items


if __name__ == "__main__":
    items = parse_customer_inventory_csv(
        "data/sample_files/customer_inventory.csv"
    )

    for item in items:
        print(item)