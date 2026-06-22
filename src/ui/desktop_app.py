"""
desktop_app.py

Desktop interface for the Modula WMS Data Integration Agent.
"""

import json
import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from agents.integration_workflow_manager import IntegrationWorkflowManager
from agents.rest_api_integration_workflow import RestApiIntegrationWorkflow
from agents.sql_integration_workflow import SQLIntegrationWorkflow
from agents.rest_profile_generator import save_rest_profile
from agents.customer_local_app_generator import generate_customer_local_app
from agents.agents.customer_order_export_agent import (
    export_orders_back_to_customer_format,
)
from agents.agents.export_ordini_monitor_agent import (
    scan_wms_export_folder_once,
)


class ModulaIntegrationApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Modula WMS Agentic AI Integration Builder")
        self.root.geometry("1000x850")

        self.workflow_manager = IntegrationWorkflowManager()
        self.rest_api_workflow = RestApiIntegrationWorkflow()
        self.sql_integration_workflow = SQLIntegrationWorkflow()

        self._build_ui()

    def _build_ui(self):
        tk.Label(
            self.root,
            text="Modula WMS Agentic AI Integration Builder",
            font=("Arial", 18, "bold"),
        ).pack(pady=15)

        tk.Label(
            self.root,
            text=(
                "Build customer integrations, manage local automation tools, "
                "and process Modula WMS import/export workflows."
            ),
            font=("Arial", 10),
            wraplength=850,
            justify="center",
        ).pack(pady=5)

        tk.Label(
            self.root,
            text="Integration Setup",
            font=("Arial", 12, "bold"),
        ).pack(pady=(20, 5))

        tk.Button(
            self.root,
            text="Build New Integration",
            command=self.show_build_integration_menu,
            width=55,
            height=2,
        ).pack(pady=6)

        tk.Label(
            self.root,
            text="Customer Automation",
            font=("Arial", 12, "bold"),
        ).pack(pady=(20, 5))

        tk.Button(
            self.root,
            text="Manage Customer Integrations",
            command=self.show_customer_integration_manager,
            width=55,
            height=2,
        ).pack(pady=6)

        tk.Label(
            self.root,
            text="Existing Integration Tools",
            font=("Arial", 12, "bold"),
        ).pack(pady=(20, 5))

        tk.Button(
            self.root,
            text="Run Existing Integration Tools",
            command=self.show_existing_tools_menu,
            width=55,
            height=2,
        ).pack(pady=6)

        self.output_text = tk.Text(self.root, height=28, width=115)
        self.output_text.pack(pady=20)

    def show_build_integration_menu(self):
        choice = simpledialog.askstring(
            "Build New Integration",
            (
                "Choose integration type:\n\n"
                "1 = Upload File / REST API Documentation\n"
                "2 = Connect to Live REST API\n"
                "3 = SQL / ODBC Integration\n"
                "4 = Generate REST Integration Package\n"
                "5 = Generate SQL Integration Package"
            ),
            parent=self.root,
        )

        if not choice:
            return

        choice = choice.strip()

        if choice == "1":
            self.upload_source_and_build_integration()
        elif choice == "2":
            self.connect_live_rest_api_ui()
        elif choice == "3":
            self.run_sql_integration()
        elif choice == "4":
            self.generate_rest_integration_package_ui()
        elif choice == "5":
            self.generate_sql_integration_package_ui()
        else:
            messagebox.showwarning(
                "Invalid Choice",
                "Please enter 1, 2, 3, 4, or 5.",
            )

    def generate_rest_integration_package_ui(self):
        customer_name = simpledialog.askstring(
            "REST Integration Package",
            "Enter customer name:",
            parent=self.root,
        )

        if not customer_name:
            return

        pull_url = simpledialog.askstring(
            "REST Pull URL",
            "Enter REST pull URL:",
            parent=self.root,
        )

        if not pull_url:
            return

        push_url = simpledialog.askstring(
            "REST Push URL",
            "Enter REST push URL:",
            parent=self.root,
        )

        if not push_url:
            return

        push_source_path = filedialog.askopenfilename(
            title="Select WMS Export Source File For REST Push",
            filetypes=[
                ("Supported Files", "*.csv *.json"),
                ("CSV Files", "*.csv"),
                ("JSON Files", "*.json"),
                ("All Files", "*.*"),
            ],
        )

        if not push_source_path:
            return

        mapping_text = simpledialog.askstring(
            "Push Field Mapping",
            (
                "Enter push field mapping as JSON.\n\n"
                "Example:\n"
                '{'
                '"order_id":"id", '
                '"customer_name":"customer.name", '
                '"item":"lines[0].sku", '
                '"quantity":"lines[0].qty"'
                '}'
            ),
            parent=self.root,
        )

        if not mapping_text:
            return

        try:
            push_field_mapping = json.loads(mapping_text)
        except json.JSONDecodeError as error:
            messagebox.showerror(
                "Invalid JSON",
                f"Field mapping was not valid JSON:\n{error}",
            )
            return

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(
            tk.END,
            "Generating REST integration package...\n\n",
        )

        try:
            result = self.rest_api_workflow.generate_manual_package(
                customer_name=customer_name,
                pull_url=pull_url,
                push_url=push_url,
                push_source_path=push_source_path,
                push_field_mapping=push_field_mapping,
            )

            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, "REST INTEGRATION PACKAGE COMPLETE\n")
            self.output_text.insert(tk.END, "=" * 70 + "\n\n")
            self.output_text.insert(tk.END, json.dumps(result, indent=4))

            messagebox.showinfo(
                "REST Package Generated",
                f"REST package generated for {customer_name}.",
            )

        except Exception as error:
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, "REST package generation failed:\n\n")
            self.output_text.insert(tk.END, str(error))
            messagebox.showerror("REST Package Error", str(error))

    def generate_sql_integration_package_ui(self):
        customer_name = simpledialog.askstring(
            "SQL Integration Package",
            "Enter customer name:",
            parent=self.root,
        )

        if not customer_name:
            return

        database_type = simpledialog.askstring(
            "Database Type",
            "Enter database type: sqlite, sql_server, or odbc",
            parent=self.root,
        )

        if not database_type:
            database_type = "sqlite"

        database_type = database_type.strip().lower()

        connection_string = simpledialog.askstring(
            "Connection String",
            "Enter SQL connection string. For SQLite, enter the .db file path:",
            parent=self.root,
        )

        if not connection_string:
            return

        pull_query = simpledialog.askstring(
            "Pull Query",
            "Enter SQL SELECT query for the pull runner:",
            parent=self.root,
        )

        if not pull_query:
            return

        push_source_path = filedialog.askopenfilename(
            title="Select CSV or JSON Source File For SQL Push",
            filetypes=[
                ("Supported Files", "*.csv *.json"),
                ("CSV Files", "*.csv"),
                ("JSON Files", "*.json"),
                ("All Files", "*.*"),
            ],
        )

        if not push_source_path:
            return

        push_target_table = simpledialog.askstring(
            "Target Table",
            "Enter destination SQL table name:",
            parent=self.root,
        )

        if not push_target_table:
            return

        mapping_text = simpledialog.askstring(
            "SQL Push Field Mapping",
            (
                "Enter SQL push field mapping as JSON.\n\n"
                "Example:\n"
                '{'
                '"order_id":"order_id", '
                '"customer_name":"customer_name", '
                '"item":"item", '
                '"quantity":"quantity"'
                '}'
            ),
            parent=self.root,
        )

        if not mapping_text:
            return

        try:
            push_field_mapping = json.loads(mapping_text)
        except json.JSONDecodeError as error:
            messagebox.showerror(
                "Invalid JSON",
                f"Field mapping was not valid JSON:\n{error}",
            )
            return

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(
            tk.END,
            "Generating SQL integration package...\n\n",
        )

        try:
            result = self.sql_integration_workflow.generate_manual_package(
                customer_name=customer_name,
                connection_string=connection_string,
                database_type=database_type,
                pull_query=pull_query,
                push_source_path=push_source_path,
                push_target_table=push_target_table,
                push_field_mapping=push_field_mapping,
            )

            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, "SQL INTEGRATION PACKAGE COMPLETE\n")
            self.output_text.insert(tk.END, "=" * 70 + "\n\n")
            self.output_text.insert(tk.END, json.dumps(result, indent=4))

            messagebox.showinfo(
                "SQL Package Generated",
                f"SQL package generated for {customer_name}.",
            )

        except Exception as error:
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, "SQL package generation failed:\n\n")
            self.output_text.insert(tk.END, str(error))
            messagebox.showerror("SQL Package Error", str(error))

    def show_existing_tools_menu(self):
        choice = simpledialog.askstring(
            "Run Existing Integration Tools",
            (
                "Choose tool:\n\n"
                "1 = Scan WMS Export Ordini Folder\n"
                "2 = Manual Export Orders Back To Customer Format"
            ),
            parent=self.root,
        )

        if not choice:
            return

        choice = choice.strip()

        if choice == "1":
            self.scan_wms_export_ordini_folder_ui()
        elif choice == "2":
            self.export_orders_back_to_customer_format_ui()
        else:
            messagebox.showwarning(
                "Invalid Choice",
                "Please enter 1 or 2.",
            )

    def get_generated_integrations_folder(self) -> Path:
        return PROJECT_ROOT / "generated_integrations"

    def get_customer_package_folder(self, customer_name: str) -> Path:
        safe_name = customer_name.strip().lower().replace(" ", "_")
        return self.get_generated_integrations_folder() / safe_name

    def load_customer_statuses(self) -> list[dict]:
        integrations_folder = self.get_generated_integrations_folder()

        if not integrations_folder.exists():
            return []

        statuses = []

        for customer_folder in sorted(integrations_folder.iterdir()):
            if not customer_folder.is_dir():
                continue

            status_path = customer_folder / "status.json"
            config_path = customer_folder / "local_agent_config.json"

            customer_name = customer_folder.name
            status_data = {
                "customer_name": customer_name,
                "safe_customer_name": customer_folder.name,
                "status": "not_started",
                "last_run": None,
                "last_success": None,
                "last_error": None,
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "package_folder": str(customer_folder),
                "status_path": str(status_path),
            }

            if config_path.exists():
                try:
                    with open(config_path, "r", encoding="utf-8") as file:
                        config = json.load(file)

                    status_data["customer_name"] = config.get(
                        "customer_name",
                        customer_name,
                    )
                    status_data["source_type"] = config.get("source_type")
                except Exception as error:
                    status_data["status"] = "config_error"
                    status_data["last_error"] = str(error)

            if status_path.exists():
                try:
                    with open(status_path, "r", encoding="utf-8") as file:
                        saved_status = json.load(file)

                    status_data.update(saved_status)
                except Exception as error:
                    status_data["status"] = "status_error"
                    status_data["last_error"] = str(error)

            statuses.append(status_data)

        return statuses

    def format_status_dashboard(self, statuses: list[dict]) -> str:
        if not statuses:
            return (
                "NO GENERATED CUSTOMER INTEGRATIONS FOUND\n"
                + "=" * 80
                + "\n\n"
                + "No folders were found inside generated_integrations/.\n"
                + "Build or generate a customer local app first."
            )

        lines = []
        lines.append("CUSTOMER INTEGRATION STATUS DASHBOARD")
        lines.append("=" * 100)
        lines.append("")

        header = (
            f"{'Customer':<18}"
            f"{'Status':<15}"
            f"{'Source':<12}"
            f"{'Last Run':<28}"
            f"{'Last Success':<28}"
            f"{'Success':<10}"
            f"{'Failed':<10}"
        )

        lines.append(header)
        lines.append("-" * 100)

        for status in statuses:
            customer = str(status.get("customer_name", ""))[:17]
            health = str(status.get("status", "unknown"))[:14]
            source = str(status.get("source_type", ""))[:11]
            last_run = str(status.get("last_run", ""))[:27]
            last_success = str(status.get("last_success", ""))[:27]
            successful_runs = str(status.get("successful_runs", 0))
            failed_runs = str(status.get("failed_runs", 0))

            lines.append(
                f"{customer:<18}"
                f"{health:<15}"
                f"{source:<12}"
                f"{last_run:<28}"
                f"{last_success:<28}"
                f"{successful_runs:<10}"
                f"{failed_runs:<10}"
            )

        lines.append("")
        lines.append("DETAILS")
        lines.append("=" * 100)

        for status in statuses:
            lines.append("")
            lines.append(f"Customer: {status.get('customer_name')}")
            lines.append(f"Status: {status.get('status')}")
            lines.append(f"Package Folder: {status.get('package_folder')}")
            lines.append(f"Last Run: {status.get('last_run')}")
            lines.append(f"Last Success: {status.get('last_success')}")
            lines.append(f"Last Error: {status.get('last_error')}")

        return "\n".join(lines)

    def refresh_customer_dashboard(self):
        statuses = self.load_customer_statuses()
        dashboard_text = self.format_status_dashboard(statuses)

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, dashboard_text)

    def ask_customer_name_for_action(self) -> str | None:
        statuses = self.load_customer_statuses()

        if not statuses:
            messagebox.showwarning(
                "No Integrations",
                "No generated customer integrations were found.",
            )
            return None

        customer_names = [status.get("customer_name") for status in statuses]
        customer_list = "\n".join(customer_names)

        customer_name = simpledialog.askstring(
            "Customer Integration",
            f"Enter customer name:\n\nAvailable:\n{customer_list}",
            parent=self.root,
        )

        if not customer_name:
            return None

        return customer_name.strip()

    def run_customer_agent_command(
        self,
        customer_name: str,
        args: list[str],
        wait_for_completion: bool = True,
    ):
        package_folder = self.get_customer_package_folder(customer_name)
        safe_name = customer_name.strip().lower().replace(" ", "_")
        runner_path = package_folder / f"run_{safe_name}_local_agent.py"

        if not runner_path.exists():
            messagebox.showerror(
                "Runner Not Found",
                f"Could not find runner:\n{runner_path}",
            )
            return

        command = [sys.executable, str(runner_path)] + args

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(
            tk.END,
            "Running command:\n\n" + " ".join(command) + "\n\n",
        )

        try:
            if wait_for_completion:
                result = subprocess.run(
                    command,
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True,
                )

                self.output_text.insert(tk.END, "STDOUT:\n")
                self.output_text.insert(tk.END, result.stdout or "")
                self.output_text.insert(tk.END, "\n\nSTDERR:\n")
                self.output_text.insert(tk.END, result.stderr or "")

                self.refresh_customer_dashboard()

                if result.returncode == 0:
                    messagebox.showinfo(
                        "Command Complete",
                        "Customer agent command completed.",
                    )
                else:
                    messagebox.showwarning(
                        "Command Failed",
                        f"Command exited with code {result.returncode}.",
                    )
            else:
                subprocess.Popen(
                    command,
                    cwd=PROJECT_ROOT,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )

                self.output_text.insert(
                    tk.END,
                    "Watch mode started in a separate console window.\n",
                )

                messagebox.showinfo(
                    "Watch Mode Started",
                    "Watch mode started in a separate console window.",
                )

        except Exception as error:
            self.output_text.insert(tk.END, f"\nCommand failed:\n{error}")
            messagebox.showerror("Command Error", str(error))

    def run_selected_customer_once(self):
        customer_name = self.ask_customer_name_for_action()

        if not customer_name:
            return

        self.run_customer_agent_command(
            customer_name=customer_name,
            args=["--once"],
            wait_for_completion=True,
        )

    def watch_selected_customer(self):
        customer_name = self.ask_customer_name_for_action()

        if not customer_name:
            return

        poll_seconds = simpledialog.askinteger(
            "Watch Mode",
            "Polling interval in seconds:",
            parent=self.root,
            initialvalue=10,
        )

        if not poll_seconds:
            poll_seconds = 10

        self.run_customer_agent_command(
            customer_name=customer_name,
            args=["--watch", "--poll-seconds", str(poll_seconds)],
            wait_for_completion=False,
        )

    def reset_selected_customer_file_state(self):
        customer_name = self.ask_customer_name_for_action()

        if not customer_name:
            return

        self.run_customer_agent_command(
            customer_name=customer_name,
            args=["--reset-file-state"],
            wait_for_completion=True,
        )

    def reset_selected_customer_rest_state(self):
        customer_name = self.ask_customer_name_for_action()

        if not customer_name:
            return

        self.run_customer_agent_command(
            customer_name=customer_name,
            args=["--reset-rest-state"],
            wait_for_completion=True,
        )

    def reset_selected_customer_wms_export_state(self):
        customer_name = self.ask_customer_name_for_action()

        if not customer_name:
            return

        self.run_customer_agent_command(
            customer_name=customer_name,
            args=["--reset-wms-export-state"],
            wait_for_completion=True,
        )

    def open_selected_customer_folder(self):
        customer_name = self.ask_customer_name_for_action()

        if not customer_name:
            return

        package_folder = self.get_customer_package_folder(customer_name)

        if not package_folder.exists():
            messagebox.showerror(
                "Folder Not Found",
                f"Could not find folder:\n{package_folder}",
            )
            return

        os.startfile(package_folder)

    def view_selected_customer_log(self):
        customer_name = self.ask_customer_name_for_action()

        if not customer_name:
            return

        package_folder = self.get_customer_package_folder(customer_name)
        log_path = package_folder / "logs" / "local_agent.log"

        if not log_path.exists():
            messagebox.showwarning(
                "Log Not Found",
                f"No log file found at:\n{log_path}",
            )
            return

        with open(log_path, "r", encoding="utf-8") as file:
            log_text = file.read()

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, f"LOG FILE: {log_path}\n")
        self.output_text.insert(tk.END, "=" * 100 + "\n\n")
        self.output_text.insert(tk.END, log_text)

    def show_customer_integration_manager(self):
        manager = tk.Toplevel(self.root)
        manager.title("Manage Customer Integrations")
        manager.geometry("700x475")
        manager.grab_set()

        tk.Label(
            manager,
            text="Customer Integration Manager",
            font=("Arial", 16, "bold"),
        ).pack(pady=15)

        tk.Label(
            manager,
            text=(
                "View generated customer agent health, run agents manually, "
                "start watch mode, reset state files, or inspect logs."
            ),
            font=("Arial", 10),
            wraplength=620,
            justify="center",
        ).pack(pady=5)

        button_frame = tk.Frame(manager)
        button_frame.pack(pady=20)

        tk.Button(
            button_frame,
            text="Refresh Dashboard",
            command=self.refresh_customer_dashboard,
            width=32,
            height=2,
        ).grid(row=0, column=0, padx=8, pady=8)

        tk.Button(
            button_frame,
            text="Run Customer Once",
            command=self.run_selected_customer_once,
            width=32,
            height=2,
        ).grid(row=0, column=1, padx=8, pady=8)

        tk.Button(
            button_frame,
            text="Start Customer Watch Mode",
            command=self.watch_selected_customer,
            width=32,
            height=2,
        ).grid(row=1, column=0, padx=8, pady=8)

        tk.Button(
            button_frame,
            text="View Customer Log",
            command=self.view_selected_customer_log,
            width=32,
            height=2,
        ).grid(row=1, column=1, padx=8, pady=8)

        tk.Button(
            button_frame,
            text="Open Customer Folder",
            command=self.open_selected_customer_folder,
            width=32,
            height=2,
        ).grid(row=2, column=0, padx=8, pady=8)

        tk.Button(
            button_frame,
            text="Reset File State",
            command=self.reset_selected_customer_file_state,
            width=32,
            height=2,
        ).grid(row=2, column=1, padx=8, pady=8)

        tk.Button(
            button_frame,
            text="Reset REST State",
            command=self.reset_selected_customer_rest_state,
            width=32,
            height=2,
        ).grid(row=3, column=0, padx=8, pady=8)

        tk.Button(
            button_frame,
            text="Reset WMS Export State",
            command=self.reset_selected_customer_wms_export_state,
            width=32,
            height=2,
        ).grid(row=3, column=1, padx=8, pady=8)

        tk.Button(
            manager,
            text="Close",
            command=manager.destroy,
            width=25,
            height=2,
        ).pack(pady=15)

        self.refresh_customer_dashboard()

    def connect_live_rest_api_ui(self):
        base_url = simpledialog.askstring(
            "Live REST API",
            "Enter the API base URL:",
            parent=self.root,
        )

        if not base_url:
            return

        endpoint = simpledialog.askstring(
            "API Endpoint",
            "Enter endpoint, for example: /posts/1 or /orders",
            parent=self.root,
        )

        if not endpoint:
            return

        auth_type = simpledialog.askstring(
            "Authentication",
            "Authentication type: none, api_key, bearer, or basic",
            parent=self.root,
        )

        if not auth_type:
            auth_type = "none"

        auth_type = auth_type.strip().lower()

        api_key = None
        api_key_header = "Authorization"
        bearer_token = None
        username = None
        password = None

        if auth_type == "api_key":
            api_key_header = simpledialog.askstring(
                "API Key Header",
                "Header name, for example: X-API-Key or Authorization",
                parent=self.root,
            ) or "Authorization"

            api_key = simpledialog.askstring(
                "API Key",
                "Enter API key:",
                parent=self.root,
            )

        elif auth_type == "bearer":
            bearer_token = simpledialog.askstring(
                "Bearer Token",
                "Enter bearer token:",
                parent=self.root,
            )

        elif auth_type == "basic":
            username = simpledialog.askstring(
                "Username",
                "Enter username:",
                parent=self.root,
            )

            password = simpledialog.askstring(
                "Password",
                "Enter password:",
                parent=self.root,
                show="*",
            )

        elif auth_type != "none":
            messagebox.showwarning(
                "Invalid Authentication Type",
                "Please enter one of: none, api_key, bearer, basic.",
            )
            return

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, "Running live REST API workflow...\n\n")

        try:
            result = self.workflow_manager.run_live_rest_api_workflow(
                base_url=base_url,
                endpoint=endpoint,
                auth_type=auth_type,
                api_key=api_key,
                api_key_header=api_key_header,
                bearer_token=bearer_token,
                username=username,
                password=password,
            )

            if result.get("status") == "success" and result.get("mapping_result"):
                mapping_result = {
                    "field_mapping": result["mapping_result"],
                    "mapping_confidence": {},
                    "mapping_notes": {},
                }

                confirmed_mapping = self.review_mapping_in_app(mapping_result)
                result["confirmed_mapping"] = confirmed_mapping

                customer_name = simpledialog.askstring(
                    "Customer Name",
                    "Enter customer name for this REST integration:",
                    parent=self.root,
                )

                if customer_name:
                    profile_path = save_rest_profile(
                        customer_name=customer_name,
                        confirmed_mapping=confirmed_mapping,
                    )

                    pagination_strategy = simpledialog.askstring(
                        "Pagination",
                        "Pagination strategy: none, page_number, or next_link",
                        parent=self.root,
                    )

                    if not pagination_strategy:
                        pagination_strategy = "none"

                    pagination_strategy = pagination_strategy.strip().lower()

                    results_key = simpledialog.askstring(
                        "Results Key",
                        (
                            "Enter results key if API wraps records, for example: "
                            "data or results. Leave blank if not needed."
                        ),
                        parent=self.root,
                    )

                    if not results_key:
                        results_key = None

                    max_pages = simpledialog.askinteger(
                        "Max Pages",
                        "Maximum pages to fetch:",
                        parent=self.root,
                        initialvalue=10,
                    )

                    if not max_pages:
                        max_pages = 10

                    package_result = generate_customer_local_app(
                        customer_name=customer_name,
                        customer_profile_path=profile_path,
                        source_type="rest_api",
                        rest_api_base_url=base_url,
                        rest_api_endpoint=endpoint,
                        rest_api_auth_type=auth_type,
                        rest_api_key=api_key,
                        rest_api_key_header=api_key_header,
                        rest_api_bearer_token=bearer_token,
                        rest_api_username=username,
                        rest_api_password=password,
                        rest_api_pagination_strategy=pagination_strategy,
                        rest_api_results_key=results_key,
                        rest_api_max_pages=max_pages,
                    )

                    result["rest_profile_path"] = profile_path
                    result["package_result"] = package_result

            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, "LIVE REST API WORKFLOW COMPLETE\n")
            self.output_text.insert(tk.END, "=" * 70 + "\n\n")
            self.output_text.insert(tk.END, json.dumps(result, indent=4))

            if result.get("status") == "error":
                messagebox.showwarning(
                    "REST API Workflow Failed",
                    result.get("message", "Unknown REST API workflow error."),
                )
            else:
                messagebox.showinfo(
                    "REST API Workflow Complete",
                    "Live REST API workflow completed successfully.",
                )

        except Exception as error:
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, "Live REST API workflow failed:\n\n")
            self.output_text.insert(tk.END, str(error))
            messagebox.showerror("REST API Error", str(error))

    def upload_source_and_build_integration(self):
        file_path = filedialog.askopenfilename(
            title="Upload Customer Source or API Documentation",
            filetypes=[
                ("Supported Sources", "*.csv *.json *.xml *.txt *.md *.yaml *.yml"),
                ("Data Files", "*.csv *.json *.xml"),
                ("API Documentation", "*.txt *.md *.json *.yaml *.yml"),
                ("All Files", "*.*"),
            ],
        )

        if not file_path:
            return

        customer_name = simpledialog.askstring(
            "Customer Name",
            "Enter customer name. For API documentation, this can be blank:",
            parent=self.root,
        )

        if customer_name is None:
            return

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, "Running file / API workflow...\n\n")

        try:
            result = self.workflow_manager.run_file_workflow(
                file_path=file_path,
                customer_name=customer_name,
                mapping_confirmation_callback=self.review_mapping_in_app,
            )

            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, "FILE / API WORKFLOW COMPLETE\n")
            self.output_text.insert(tk.END, "=" * 70 + "\n\n")
            self.output_text.insert(tk.END, json.dumps(result, indent=4))

            if result.get("status") == "error":
                messagebox.showwarning(
                    "Workflow Failed",
                    result.get("message", "Unknown workflow error."),
                )
            else:
                messagebox.showinfo(
                    "Workflow Complete",
                    "Workflow completed successfully.",
                )

        except Exception as error:
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, "Workflow failed:\n\n")
            self.output_text.insert(tk.END, str(error))
            messagebox.showerror("Workflow Error", str(error))

    def scan_wms_export_ordini_folder_ui(self):
        watch_folder = filedialog.askdirectory(
            title="Select WMS Export Ordini Folder",
            initialdir="data/wms_exports",
        )

        if not watch_folder:
            return

        customer_name = simpledialog.askstring(
            "Customer Name",
            "Enter customer name for this WMS export:",
            parent=self.root,
        )

        if not customer_name:
            return

        output_folder = filedialog.askdirectory(
            title="Select Customer Export Output Folder",
            initialdir="data/customer_exports",
        )

        if not output_folder:
            return

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, "Scanning WMS export ordini folder...\n\n")

        try:
            results = scan_wms_export_folder_once(
                watch_folder=watch_folder,
                customer_name=customer_name,
                output_folder=output_folder,
            )

            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, "WMS EXPORT ORDINI SCAN COMPLETE\n")
            self.output_text.insert(tk.END, "=" * 70 + "\n\n")
            self.output_text.insert(tk.END, json.dumps(results, indent=4))

            messagebox.showinfo(
                "Scan Complete",
                f"Processed {len(results)} WMS export file(s).",
            )

        except Exception as error:
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, "WMS export scan failed:\n\n")
            self.output_text.insert(tk.END, str(error))
            messagebox.showerror("WMS Export Scan Error", str(error))

    def export_orders_back_to_customer_format_ui(self):
        customer_profile_path = filedialog.askopenfilename(
            title="Select Customer Profile",
            filetypes=[
                ("JSON Files", "*.json"),
                ("All Files", "*.*"),
            ],
            initialdir="configs/customers",
        )

        if not customer_profile_path:
            return

        internal_orders_path = filedialog.askopenfilename(
            title="Select Internal Orders JSON",
            filetypes=[
                ("JSON Files", "*.json"),
                ("All Files", "*.*"),
            ],
            initialdir="data/processed",
        )

        if not internal_orders_path:
            return

        output_path = filedialog.asksaveasfilename(
            title="Save Customer Export CSV",
            defaultextension=".csv",
            filetypes=[
                ("CSV Files", "*.csv"),
                ("All Files", "*.*"),
            ],
            initialdir="data/output",
            initialfile="customer_orders_export.csv",
        )

        if not output_path:
            return

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(
            tk.END,
            "Exporting ordini/orders back to customer format...\n\n",
        )

        try:
            result = export_orders_back_to_customer_format(
                customer_profile_path=customer_profile_path,
                internal_orders_path=internal_orders_path,
                output_path=output_path,
            )

            self.output_text.delete("1.0", tk.END)

            if result.get("status") == "skipped":
                self.output_text.insert(tk.END, "CUSTOMER EXPORT SKIPPED\n")
                self.output_text.insert(tk.END, "=" * 70 + "\n\n")
                self.output_text.insert(tk.END, json.dumps(result, indent=4))

                messagebox.showinfo(
                    "Export Skipped",
                    result.get(
                        "reason",
                        "Only ordini/order imports are exported. Articoli/item imports are skipped.",
                    ),
                )
                return

            self.output_text.insert(tk.END, "CUSTOMER ORDER EXPORT COMPLETE\n")
            self.output_text.insert(tk.END, "=" * 70 + "\n\n")
            self.output_text.insert(tk.END, json.dumps(result, indent=4))

            messagebox.showinfo(
                "Export Complete",
                f"Orders exported successfully.\n\nOutput:\n{result.get('output_path')}",
            )

        except Exception as error:
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, "Customer export failed:\n\n")
            self.output_text.insert(tk.END, str(error))
            messagebox.showerror("Customer Export Error", str(error))

    def review_mapping_in_app(self, mapping_result: dict) -> dict:
        messagebox.showinfo(
            "LLM Mapping Suggestions Ready",
            "The LLM suggested field mappings. Please review and confirm them.",
        )

        dialog = tk.Toplevel(self.root)
        dialog.title("Confirm Field Mappings")
        dialog.geometry("950x575")
        dialog.grab_set()

        tk.Label(
            dialog,
            text="Review and Confirm LLM-Suggested Field Mappings",
            font=("Arial", 14, "bold"),
        ).pack(pady=10)

        tk.Label(
            dialog,
            text="Edit the customer field values if needed, then click Confirm Mappings.",
            font=("Arial", 10),
        ).pack(pady=5)

        frame = tk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        field_mapping = mapping_result.get("field_mapping", {})
        mapping_confidence = mapping_result.get("mapping_confidence", {})
        mapping_notes = mapping_result.get("mapping_notes", {})

        entries = {}

        header = tk.Frame(frame)
        header.pack(fill=tk.X, pady=5)

        tk.Label(
            header,
            text="Modula Field",
            width=25,
            anchor="w",
            font=("Arial", 10, "bold"),
        ).pack(side=tk.LEFT)

        tk.Label(
            header,
            text="Suggested Customer Field",
            width=30,
            anchor="w",
            font=("Arial", 10, "bold"),
        ).pack(side=tk.LEFT)

        tk.Label(
            header,
            text="Confidence",
            width=12,
            anchor="w",
            font=("Arial", 10, "bold"),
        ).pack(side=tk.LEFT)

        tk.Label(
            header,
            text="Reason",
            width=50,
            anchor="w",
            font=("Arial", 10, "bold"),
        ).pack(side=tk.LEFT)

        for modula_field, suggested_field in field_mapping.items():
            row = tk.Frame(frame)
            row.pack(fill=tk.X, pady=4)

            tk.Label(
                row,
                text=modula_field,
                width=25,
                anchor="w",
            ).pack(side=tk.LEFT)

            entry = tk.Entry(row, width=30)
            entry.insert(0, suggested_field or "")
            entry.pack(side=tk.LEFT, padx=5)
            entries[modula_field] = entry

            tk.Label(
                row,
                text=str(mapping_confidence.get(modula_field, "")),
                width=12,
                anchor="w",
            ).pack(side=tk.LEFT)

            tk.Label(
                row,
                text=mapping_notes.get(modula_field, ""),
                width=50,
                anchor="w",
                wraplength=375,
            ).pack(side=tk.LEFT)

        confirmed_mapping = {}

        def confirm():
            for modula_field, entry in entries.items():
                value = entry.get().strip()
                confirmed_mapping[modula_field] = value if value else None

            dialog.destroy()

        tk.Button(
            dialog,
            text="Confirm Mappings",
            command=confirm,
            width=25,
            height=2,
        ).pack(pady=15)

        self.root.wait_window(dialog)

        return confirmed_mapping

    def run_sql_integration(self):
        generate_xml = messagebox.askyesno(
            "SQL / ODBC Integration",
            (
                "Do you want to generate Modula XML from live SQL?\n\n"
                "Yes = Run Live SQL → Modula XML\n"
                "No = Analyze SQL / ODBC Connection"
            ),
        )

        if generate_xml:
            self.run_live_sql_to_xml()
        else:
            self.analyze_sql_connection()

    def analyze_sql_connection(self):
        connection_string = simpledialog.askstring(
            "SQL / ODBC Connection",
            "Enter SQL / ODBC connection string:",
            parent=self.root,
        )

        if not connection_string:
            return

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, "Analyzing SQL / ODBC connection...\n\n")

        try:
            result = self.workflow_manager.run_sql_analysis_workflow(
                connection_string=connection_string,
            )

            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, "SQL / ODBC ANALYSIS COMPLETE\n")
            self.output_text.insert(tk.END, "=" * 70 + "\n\n")
            self.output_text.insert(tk.END, json.dumps(result, indent=4))

            messagebox.showinfo(
                "SQL Analysis Complete",
                f"Output:\n{result.get('output_path')}",
            )

        except Exception as error:
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, "SQL / ODBC analysis failed:\n\n")
            self.output_text.insert(tk.END, str(error))
            messagebox.showerror("SQL Analysis Error", str(error))

    def run_live_sql_to_xml(self):
        connection_string = simpledialog.askstring(
            "Live SQL Connection",
            "Enter SQL / ODBC connection string:",
            parent=self.root,
        )

        if not connection_string:
            return

        profile_path = filedialog.askopenfilename(
            title="Select SQL Mapping Profile",
            filetypes=[
                ("JSON Files", "*.json"),
                ("All Files", "*.*"),
            ],
            initialdir="configs/customers",
        )

        if not profile_path:
            return

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, "Running Live SQL → Modula XML workflow...\n\n")

        try:
            result = self.workflow_manager.run_live_sql_to_xml_workflow(
                connection_string=connection_string,
                profile_path=profile_path,
            )

            self.output_text.delete("1.0", tk.END)

            if result.get("status") == "success":
                self.output_text.insert(tk.END, "LIVE SQL → MODULA XML COMPLETE\n")
                self.output_text.insert(tk.END, "=" * 70 + "\n\n")
                self.output_text.insert(tk.END, json.dumps(result, indent=4))

                export_path = result.get("export", {}).get("output_path")

                messagebox.showinfo(
                    "SQL XML Export Complete",
                    f"XML Generated:\n{export_path}",
                )
            else:
                self.output_text.insert(tk.END, "LIVE SQL → MODULA XML FAILED\n")
                self.output_text.insert(tk.END, "=" * 70 + "\n\n")
                self.output_text.insert(tk.END, json.dumps(result, indent=4))

                messagebox.showwarning(
                    "SQL Workflow Failed",
                    result.get("error", result.get("message", "Unknown error")),
                )

        except Exception as error:
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, "SQL workflow error:\n\n")
            self.output_text.insert(tk.END, str(error))
            messagebox.showerror("SQL Workflow Error", str(error))


if __name__ == "__main__":
    root = tk.Tk()
    app = ModulaIntegrationApp(root)
    root.mainloop()