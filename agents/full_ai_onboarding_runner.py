import json
import shutil
from pathlib import Path

from agents.integration_package_generator import generate_integration_package_from_file
from agents.openai_profile_review_agent import review_customer_profile
from src.pipeline.file_processing_pipeline import FileProcessingPipeline


def copy_file_if_exists(source_path: str | None, destination_path: Path) -> str | None:
    if not source_path:
        return None

    source = Path(source_path)

    if not source.exists():
        return None

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(source, destination_path)

    return str(destination_path)


def run_full_ai_onboarding(
    customer_name: str,
    source_type: str,
    file_path: str,
    mapping_confirmation_callback=None,
) -> dict:
    package_result = generate_integration_package_from_file(
        customer_name=customer_name,
        source_type=source_type,
        file_path=file_path,
        mapping_confirmation_callback=mapping_confirmation_callback,
    )

    integration_folder = Path(package_result["integration_folder"])
    integration_folder.mkdir(parents=True, exist_ok=True)

    source_copy_path = integration_folder / Path(file_path).name
    shutil.copy(file_path, source_copy_path)

    registered_profile_path = package_result.get("registered_profile_path")

    profile_review_result = review_customer_profile(registered_profile_path)

    profile_review_copy_path = copy_file_if_exists(
        profile_review_result.get("output_path"),
        integration_folder / "profile_review.json",
    )

    pipeline = FileProcessingPipeline()
    processing_result = pipeline.process_file(
        file_path=file_path,
        profile_path=registered_profile_path,
    )

    export_result = processing_result.get("export_result", {})
    xml_output_path = export_result.get("output_path")

    copied_xml_path = copy_file_if_exists(
        xml_output_path,
        integration_folder / "converted_modula_orders.xml",
    )

    processing_result_path = integration_folder / "processing_result.json"

    with open(processing_result_path, "w", encoding="utf-8") as file:
        json.dump(processing_result, file, indent=4)

    return {
        "status": "success",
        "customer_name": customer_name,
        "source_type": source_type,
        "integration_folder": str(integration_folder),
        "source_copy_path": str(source_copy_path),
        "registered_profile_path": registered_profile_path,
        "profile_review_copy_path": profile_review_copy_path,
        "profile_review_result": profile_review_result,
        "original_xml_output_path": xml_output_path,
        "converted_xml_path": copied_xml_path,
        "processing_result_path": str(processing_result_path),
        "processing_status": processing_result.get("status"),
        "export_status": export_result.get("status"),
        "export_result": export_result,
        "package_result": package_result,
        "processing_result": processing_result,
    }


if __name__ == "__main__":
    result = run_full_ai_onboarding(
        customer_name="Tesla",
        source_type="csv",
        file_path="data/customer_input/weird_customer.csv",
    )

    print(json.dumps(result, indent=4))