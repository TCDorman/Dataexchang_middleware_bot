import json
from datetime import datetime
from pathlib import Path

from agents.openai_field_mapping_agent import infer_field_mapping_with_openai
from src.ai.header_extraction_agent import HeaderExtractionAgent
from src.ai.profile_generation_agent import ProfileGenerationAgent


def get_safe_customer_name(customer_name: str) -> str:
    return customer_name.strip().lower().replace(" ", "_")


def get_integration_folder(customer_name: str) -> Path:
    safe_name = get_safe_customer_name(customer_name)
    return Path("generated_integrations") / safe_name


def get_registry_profile_path(customer_name: str) -> Path:
    safe_name = get_safe_customer_name(customer_name)
    return Path("configs") / "customers" / f"{safe_name}.json"


def write_json_file(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        file.write(content)


def generate_config(customer_name: str, source_type: str) -> dict:
    return {
        "customer_name": customer_name,
        "source_type": source_type,
        "target_system": "Modula WMS",
        "target_format": "XML",
        "created_at": datetime.now().isoformat(),
    }


def generate_default_mapping(source_fields: list[str] | None = None) -> dict:
    if not source_fields:
        return {
            "order_id": "",
            "customer_name": "",
            "ship_to_name": "",
            "ship_to_address": "",
            "item": "",
            "quantity": "",
            "location": "",
        }

    mapping_result = infer_field_mapping_with_openai(
        source_columns=source_fields,
        source_type="csv",
    )

    return mapping_result.get("field_mapping", {})


def apply_confirmed_mapping_to_result(
    mapping_result: dict,
    confirmed_mapping: dict,
) -> dict:
    updated_mapping_result = dict(mapping_result)
    updated_mapping_result["field_mapping"] = confirmed_mapping
    updated_mapping_result["mapping_method"] = (
        f"{mapping_result.get('mapping_method', 'unknown')}_confirmed"
    )
    updated_mapping_result["confirmed_by_user"] = True
    updated_mapping_result["confirmed_at"] = datetime.now().isoformat(
        timespec="seconds"
    )

    return updated_mapping_result


def write_mapping_confirmation_file(
    path: Path,
    mapping_result: dict,
    confirmed_mapping: dict,
) -> dict:
    confirmation_result = {
        "status": "confirmed",
        "confirmed_at": datetime.now().isoformat(timespec="seconds"),
        "original_mapping_result": mapping_result,
        "confirmed_field_mapping": confirmed_mapping,
    }

    write_json_file(path, confirmation_result)

    return confirmation_result


def generate_customer_profile(
    customer_name: str,
    source_type: str,
    source_fields: list[str],
    mapping_result: dict,
) -> dict:
    field_mapping = mapping_result.get("field_mapping", {})
    mapping_confidence = mapping_result.get("mapping_confidence", {})
    mapping_notes = mapping_result.get("mapping_notes", {})

    agent = ProfileGenerationAgent()

    profile = agent.generate_profile(
        customer_name=customer_name,
        source_type=source_type,
        headers=source_fields,
        field_mapping=field_mapping,
    )

    profile["field_mapping"] = field_mapping
    profile["mapping_confidence"] = mapping_confidence
    profile["mapping_notes"] = mapping_notes
    profile["mapping_method"] = mapping_result.get("mapping_method")
    profile["fallback_reason"] = mapping_result.get("fallback_reason")
    profile["confirmed_by_user"] = mapping_result.get("confirmed_by_user", False)
    profile["confirmed_at"] = mapping_result.get("confirmed_at")

    return profile


def generate_readme(customer_name: str, source_type: str) -> str:
    return f"""# {customer_name} Integration Package

This folder was generated automatically by the Modula WMS Data Integration Agent.

## Customer
{customer_name}

## Source Type
{source_type}

## Target System
Modula WMS

## Files
- config.json: customer integration settings
- mapping.json: user-confirmed field mapping from customer file to Modula WMS fields
- mapping_confirmation.json: audit trail of LLM suggestion and user confirmation
- customer_profile.json: AI-generated customer profile with validation rules and mapping notes
- configs/customers profile copy: registered profile used by the processing pipeline

## Next Step
Review customer_profile.json and mapping.json, then run the integration pipeline.
"""


def generate_integration_package(
    customer_name: str,
    source_type: str,
    source_fields: list[str] | None = None,
    mapping_confirmation_callback=None,
) -> dict:
    folder = get_integration_folder(customer_name)

    config_path = folder / "config.json"
    mapping_path = folder / "mapping.json"
    confirmation_path = folder / "mapping_confirmation.json"
    profile_path = folder / "customer_profile.json"
    registry_profile_path = get_registry_profile_path(customer_name)
    readme_path = folder / "README.md"

    config = generate_config(customer_name, source_type)
    confirmation_result = None

    if source_fields:
        mapping_result = infer_field_mapping_with_openai(
            source_columns=source_fields,
            source_type=source_type,
        )

        if mapping_confirmation_callback:
            confirmed_mapping = mapping_confirmation_callback(mapping_result)

            confirmation_result = write_mapping_confirmation_file(
                path=confirmation_path,
                mapping_result=mapping_result,
                confirmed_mapping=confirmed_mapping,
            )

            mapping_result = apply_confirmed_mapping_to_result(
                mapping_result=mapping_result,
                confirmed_mapping=confirmed_mapping,
            )
        else:
            mapping_result["confirmed_by_user"] = False
            mapping_result["confirmed_at"] = None

        mapping = mapping_result.get("field_mapping", {})

        customer_profile = generate_customer_profile(
            customer_name=customer_name,
            source_type=source_type,
            source_fields=source_fields,
            mapping_result=mapping_result,
        )
    else:
        mapping_result = {
            "mapping_method": "empty",
            "fallback_reason": "No source fields provided.",
            "field_mapping": generate_default_mapping(None),
            "mapping_confidence": {},
            "mapping_notes": {},
            "confirmed_by_user": False,
            "confirmed_at": None,
        }

        mapping = mapping_result["field_mapping"]

        customer_profile = {
            "customer_name": customer_name,
            "source_type": source_type,
            "target_system": "Modula WMS",
            "target_format": "XML",
            "header_signature": [],
            "field_mapping": mapping,
            "validation_rules": {},
            "mapping_confidence": {},
            "mapping_notes": {},
            "mapping_method": mapping_result.get("mapping_method"),
            "fallback_reason": mapping_result.get("fallback_reason"),
            "confirmed_by_user": False,
            "confirmed_at": None,
        }

    readme = generate_readme(customer_name, source_type)

    write_json_file(config_path, config)
    write_json_file(mapping_path, mapping)
    write_json_file(profile_path, customer_profile)
    write_json_file(registry_profile_path, customer_profile)
    write_text_file(readme_path, readme)

    files_created = [
        str(config_path),
        str(mapping_path),
        str(profile_path),
        str(registry_profile_path),
        str(readme_path),
    ]

    if confirmation_result:
        files_created.insert(2, str(confirmation_path))

    return {
        "status": "success",
        "customer_name": customer_name,
        "source_type": source_type,
        "integration_folder": str(folder),
        "registered_profile_path": str(registry_profile_path),
        "files_created": files_created,
        "mapping": mapping,
        "mapping_result": mapping_result,
        "confirmation_result": confirmation_result,
        "customer_profile": customer_profile,
    }


def generate_integration_package_from_file(
    customer_name: str,
    source_type: str,
    file_path: str,
    mapping_confirmation_callback=None,
) -> dict:
    header_agent = HeaderExtractionAgent()

    source_fields = header_agent.extract_headers(file_path)

    return generate_integration_package(
        customer_name=customer_name,
        source_type=source_type,
        source_fields=source_fields,
        mapping_confirmation_callback=mapping_confirmation_callback,
    )


if __name__ == "__main__":
    result = generate_integration_package_from_file(
        customer_name="ESA_Test",
        source_type="csv",
        file_path="data/customer_input/ESA.csv",
    )

    print(json.dumps(result, indent=4))