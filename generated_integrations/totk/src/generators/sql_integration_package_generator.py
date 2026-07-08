"""
sql_integration_package_generator.py

Generates a complete SQL integration package.
"""

from pathlib import Path

from src.generators.sql_config_generator import SQLConfigGenerator
from src.generators.sql_pull_script_generator import SQLPullScriptGenerator
from src.generators.sql_push_script_generator import SQLPushScriptGenerator


class SQLIntegrationPackageGenerator:
    """
    Generates SQL pull, push, and config files.
    """

    def __init__(self):
        self.pull_generator = SQLPullScriptGenerator()
        self.push_generator = SQLPushScriptGenerator()
        self.config_generator = SQLConfigGenerator()

    def generate_package(
        self,
        customer_name: str,
        output_folder: str,
        connection_string: str,
        pull_query: str,
        push_source_path: str,
        push_target_table: str,
        push_field_mapping: dict[str, str],
        database_type: str = "sqlite",
    ) -> dict:
        package_folder = Path(output_folder)
        package_folder.mkdir(parents=True, exist_ok=True)

        pull_script_result = self.pull_generator.generate(
            customer_name=customer_name,
            output_folder=str(package_folder),
            script_name="sql_pull_runner.py",
        )

        push_script_result = self.push_generator.generate(
            customer_name=customer_name,
            output_folder=str(package_folder),
            script_name="sql_push_runner.py",
        )

        pull_config_result = self.config_generator.generate_pull_config(
            output_folder=str(package_folder),
            connection_string=connection_string,
            database_type=database_type,
            query=pull_query,
            config_name="sql_pull_config.json",
            output_path=str(package_folder / "data" / "sql_pull_output.json"),
        )

        push_config_result = self.config_generator.generate_push_config(
            output_folder=str(package_folder),
            connection_string=connection_string,
            database_type=database_type,
            source_path=push_source_path,
            target_table=push_target_table,
            field_mapping=push_field_mapping,
            config_name="sql_push_config.json",
        )

        return {
            "status": "success",
            "customer_name": customer_name,
            "package_folder": str(package_folder),
            "files": {
                "pull_script": pull_script_result["script_path"],
                "push_script": push_script_result["script_path"],
                "pull_config": pull_config_result["config_path"],
                "push_config": push_config_result["config_path"],
            },
        }