"""
rest_integration_package_generator.py

Generates a complete REST integration package.
"""

from pathlib import Path

from src.generators.readme_generator import ReadmeGenerator
from src.generators.rest_config_generator import RestConfigGenerator
from src.generators.rest_pull_script_generator import RestPullScriptGenerator
from src.generators.rest_push_script_generator import RestPushScriptGenerator
from src.generators.scheduler_scaffold_generator import SchedulerScaffoldGenerator


class RestIntegrationPackageGenerator:
    """
    Generates REST pull, push, scheduler, config, and README files.
    """

    def __init__(self):
        self.pull_generator = RestPullScriptGenerator()
        self.push_generator = RestPushScriptGenerator()
        self.config_generator = RestConfigGenerator()
        self.scheduler_generator = SchedulerScaffoldGenerator()
        self.readme_generator = ReadmeGenerator()

    def generate_package(
        self,
        customer_name: str,
        output_folder: str,
        pull_url: str,
        push_url: str,
        push_source_path: str,
        push_field_mapping: dict[str, str],
    ) -> dict:
        package_folder = Path(output_folder)
        package_folder.mkdir(parents=True, exist_ok=True)

        pull_script_result = self.pull_generator.generate(
            customer_name=customer_name,
            output_folder=str(package_folder),
            script_name="rest_pull_runner.py",
        )

        push_script_result = self.push_generator.generate(
            customer_name=customer_name,
            output_folder=str(package_folder),
            script_name="rest_push_runner.py",
        )

        pull_config_result = self.config_generator.generate_pull_config(
            output_folder=str(package_folder),
            url=pull_url,
            config_name="rest_pull_config.json",
            output_data_folder=str(package_folder / "data" / "rest_pull_output"),
            log_path=str(package_folder / "logs" / "rest_pull_runner.log"),
        )

        push_config_result = self.config_generator.generate_push_config(
            output_folder=str(package_folder),
            url=push_url,
            source_path=push_source_path,
            field_mapping=push_field_mapping,
            config_name="rest_push_config.json",
            log_path=str(package_folder / "logs" / "rest_push_runner.log"),
            dead_letter_folder=str(package_folder / "data" / "dead_letter"),
        )

        pull_scheduler_result = self.scheduler_generator.generate(
            customer_name=customer_name,
            output_folder=str(package_folder),
            target_script=str(package_folder / "rest_pull_runner.py"),
            config_path=str(package_folder / "rest_pull_config.json"),
            script_name="rest_pull_scheduler.py",
        )

        push_scheduler_result = self.scheduler_generator.generate(
            customer_name=customer_name,
            output_folder=str(package_folder),
            target_script=str(package_folder / "rest_push_runner.py"),
            config_path=str(package_folder / "rest_push_config.json"),
            script_name="rest_push_scheduler.py",
        )

        readme_result = self.readme_generator.generate(
            customer_name=customer_name,
            output_folder=str(package_folder),
            source_type="rest_api",
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
                "pull_scheduler": pull_scheduler_result["script_path"],
                "push_scheduler": push_scheduler_result["script_path"],
                "readme": readme_result["readme_path"],
            },
        }