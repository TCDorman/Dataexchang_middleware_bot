import json
from datetime import datetime
from pathlib import Path

from src.ai.field_mapping_agent import FieldMappingAgent
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
    target_fields = [
        "order_id",
        "customer_name",
        "item",
        "quantity",
    ]

    if not source_fields:
        return {
            "order_id": "",
            "customer_name": "",
            "item": "",
            "quantity": "",
        }

    agent = FieldMappingAgent()

    return agent.suggest_mapping(
        source_fields=source_fields,
        target_fields=target_fields,
    )


def generate_customer_profile(
    customer_name: str,
    source_type: str,
    source_fields: list[str],
    mapping: dict,
) -> dict:
    agent = ProfileGenerationAgent()

    return agent.generate_profile(
        customer_name=customer_name,
        source_type=source_type,
        headers=source_fields,
        field_mapping=mapping,
    )


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
- mapping.json: AI-suggested field mapping from customer file to Modula WMS fields
- customer_profile.json: AI-generated customer profile with validation rules and mapping notes
- configs/customers profile copy: registered profile used by the processing pipeline

## Next Step
Review customer_profile.json and mapping.json, then run the integration pipeline.
"""


def generate_integration_package(
    customer_name: str,
    source_type: str,
    source_fields: list[str] | None = None,
) -> dict:
    folder = get_integration_folder(customer_name)

    config_path = folder / "config.json"
    mapping_path = folder / "mapping.json"
    profile_path = folder / "customer_profile.json"
    registry_profile_path = get_registry_profile_path(customer_name)
    readme_path = folder / "README.md"

    config = generate_config(customer_name, source_type)
    mapping = generate_default_mapping(source_fields)

    if source_fields:
        customer_profile = generate_customer_profile(
            customer_name=customer_name,
            source_type=source_type,
            source_fields=source_fields,
            mapping=mapping,
        )
    else:
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
        }

    readme = generate_readme(customer_name, source_type)

    write_json_file(config_path, config)
    write_json_file(mapping_path, mapping)
    write_json_file(profile_path, customer_profile)
    write_json_file(registry_profile_path, customer_profile)
    write_text_file(readme_path, readme)

    return {
        "status": "success",
        "customer_name": customer_name,
        "source_type": source_type,
        "integration_folder": str(folder),
        "registered_profile_path": str(registry_profile_path),
        "files_created": [
            str(config_path),
            str(mapping_path),
            str(profile_path),
            str(registry_profile_path),
            str(readme_path),
        ],
        "mapping": mapping,
        "customer_profile": customer_profile,
    }


def generate_integration_package_from_file(
    customer_name: str,
    source_type: str,
    file_path: str,
) -> dict:
    header_agent = HeaderExtractionAgent()

    source_fields = header_agent.extract_headers(file_path)

    return generate_integration_package(
        customer_name=customer_name,
        source_type=source_type,
        source_fields=source_fields,
    )


if __name__ == "__main__":
    result = generate_integration_package_from_file(
        customer_name="Tesla",
        source_type="csv",
        file_path="data/customer_input/weird_customer.csv",
    )

    print(json.dumps(result, indent=4))