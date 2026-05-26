from pathlib import Path

# ==========================================
# Modula Integration Agent Project Structure
# ==========================================

folders = [
    # Main application folders
    "app",
    "app/parsers",
    "app/mapping_engine",
    "app/transformers",
    "app/validators",
    "app/prompts",
    "app/models",
    "app/ui",

    # Sample data folders
    "sample_data",
    "sample_data/csv",
    "sample_data/xml",
    "sample_data/json",

    # Output folders
    "output",
    "output/generated_scripts",
    "output/validated_files",
    "output/logs",

    # Testing folders
    "tests",
    "tests/parsers",
    "tests/mapping_engine",
    "tests/transformers",
    "tests/validators",

    # Documentation and config
    "docs",
    "config"
]

files = [
    # Root files
    "README.md",
    ".gitignore",
    ".env.example",
    "requirements.txt",
    "main.py",

    # Python package initialization files
    "app/__init__.py",
    "app/parsers/__init__.py",
    "app/mapping_engine/__init__.py",
    "app/transformers/__init__.py",
    "app/validators/__init__.py",
    "app/prompts/__init__.py",
    "app/models/__init__.py",
    "app/ui/__init__.py",

    # Documentation files
    "docs/architecture.md",
    "docs/wms_field_reference.md",

    # Configuration files
    "config/wms_metadata.json"
]

# Create folders
for folder in folders:
    Path(folder).mkdir(parents=True, exist_ok=True)
    print(f"Created folder: {folder}")

# Create files
for file in files:
    Path(file).touch(exist_ok=True)
    print(f"Created file: {file}")

print("\nProject structure created successfully.")