import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools.tool_registry import TOOLS


def process_wms_export_to_customer_csv(
    wms_export_xml_path: str,
    output_csv_path: str = "data/output/customer_export_from_agent.csv",
):
    result = TOOLS["convert_wms_export_to_customer_csv"](
        wms_export_xml_path,
        output_csv_path,
    )

    return result


if __name__ == "__main__":
    result = process_wms_export_to_customer_csv(
        "data/sample_files/CFG-EXP-ORDINI.xml"
    )

    print("\nExport Result:")
    print(result)