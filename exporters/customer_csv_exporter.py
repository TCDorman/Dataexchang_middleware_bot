import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from parsers.wms_export_parser import parse_wms_order_export


def export_wms_orders_to_customer_csv(orders, output_path: str):
    rows = []

    for order in orders:
        for line in order.lines:
            rows.append(
                {
                    "order_number": order.order_number,
                    "item_code": line.item_code,
                    "quantity_completed": line.quantity,
                    "batch": line.sub1,
                    "warehouse_task": line.warehouse_task,
                    "source_bin": line.source_bin,
                    "destination_bin": line.destination_bin,
                }
            )

    df = pd.DataFrame(rows)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_file, index=False)

    return output_file


if __name__ == "__main__":
    orders = parse_wms_order_export(
        "data/sample_files/CFG-EXP-ORDINI.xml"
    )

    output_file = export_wms_orders_to_customer_csv(
        orders,
        "data/output/customer_order_export.csv",
    )

    print(f"Exported customer CSV: {output_file}")