import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.customer_router import process_customer_files
from agents.export_agent import process_wms_export_to_customer_csv
from tools.tool_registry import TOOLS


def run_customer_import(
    customer_name: str,
    file_paths: list[str],
):
    result = process_customer_files(
        customer_name,
        file_paths,
    )

    workflow_result = result["result"]

    conversion = workflow_result["conversion"]
    validation = workflow_result["validation"]

    TOOLS["write_audit_log"](
        customer_name=customer_name,
        direction="customer_to_wms",
        input_files=file_paths,
        output_file=conversion["output_path"],
        status=validation["status"],
        validation_errors=validation["errors"],
    )

    return result


def run_wms_export(
    wms_export_xml_path: str,
    output_csv_path: str = "data/output/customer_export.csv",
):
    result = process_wms_export_to_customer_csv(
        wms_export_xml_path,
        output_csv_path,
    )

    TOOLS["write_audit_log"](
        customer_name="WMS Export",
        direction="wms_to_customer",
        input_files=[wms_export_xml_path],
        output_file=result["output_path"],
        status=result["status"],
        validation_errors=[],
    )

    return result


if __name__ == "__main__":

    import_result = run_customer_import(
        "Ford",
        [
            "data/sample_files/test_ui_headers.csv",
            "data/sample_files/test_ui_lines.csv",
        ],
    )

    print("\nIMPORT RESULT")
    print(import_result)

    export_result = run_wms_export(
        "data/sample_files/CFG-EXP-ORDINI.xml",
        "data/output/customer_export.csv",
    )

    print("\nEXPORT RESULT")
    print(export_result)