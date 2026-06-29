"""
desktop_app.py

Desktop interface for the Modula WMS Agentic AI Middleware Assistant.

This UI is focused on implementation-assistant workflows:
1. Analyze customer requirements
2. Analyze uploaded source/API documentation
3. Connect to live REST API
4. Generate REST integration package
5. Generate SQL integration package
6. Analyze SQL / ODBC connection
"""

import json
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
from src.ai.requirements_analysis_agent import RequirementsAnalysisAgent


class ModulaIntegrationApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Modula WMS Agentic AI Middleware Assistant")
        self.root.geometry("1000x850")

        self.workflow_manager = IntegrationWorkflowManager()
        self.rest_api_workflow = RestApiIntegrationWorkflow()
        self.sql_integration_workflow = SQLIntegrationWorkflow()
        self.requirements_agent = RequirementsAnalysisAgent()

        self._build_ui()

    def _build_ui(self):
        tk.Label(
            self.root,
            text="Modula WMS Agentic AI Middleware Assistant",
            font=("Arial", 18, "bold"),
        ).pack(pady=15)

        tk.Label(
            self.root,
            text=(
                "Analyze customer integration requirements, generate middleware "
                "planning artifacts, and create file/REST/SQL integration packages."
            ),
            font=("Arial", 10),
            wraplength=850,
            justify="center",
        ).pack(pady=5)

        tk.Button(
            self.root,
            text="Start Middleware Assistant",
            command=self.show_build_integration_menu,
            width=55,
            height=2,
        ).pack(pady=20)

        self.output_text = tk.Text(self.root, height=34, width=115)
        self.output_text.pack(pady=20)

    def show_build_integration_menu(self):
        choice = simpledialog.askstring(
            "Middleware Assistant",
            (
                "Choose workflow:\n\n"
                "1 = Analyze Customer Requirements\n"
                "2 = Upload File / API Documentation\n"
                "3 = Connect to Live REST API\n"
                "4 = Generate REST Integration Package\n"
                "5 = Generate SQL Integration Package\n"
                "6 = SQL / ODBC Analysis"
            ),
            parent=self.root,
        )

        if not choice:
            return

        choice = choice.strip()

        if choice == "1":
            self.analyze_customer_requirements_ui()
        elif choice == "2":
            self.upload_source_and_build_integration()
        elif choice == "3":
            self.connect_live_rest_api_ui()
        elif choice == "4":
            self.generate_rest_integration_package_ui()
        elif choice == "5":
            self.generate_sql_integration_package_ui()
        elif choice == "6":
            self.analyze_sql_connection()
        else:
            messagebox.showwarning(
                "Invalid Choice",
                "Please enter 1, 2, 3, 4, 5, or 6.",
            )

    def analyze_customer_requirements_ui(self):
        requirements_text = simpledialog.askstring(
            "Analyze Customer Requirements",
            (
                "Paste customer integration requirements.\n\n"
                "Example:\n"
                "Customer uses SAP. Orders arrive as CSV. "
                "Inventory transactions go back through REST. "
                "Serialized products require serial number tracking."
            ),
            parent=self.root,
        )

        if not requirements_text:
            return

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(
            tk.END,
            "Analyzing customer requirements with OpenAI...\n\n",
        )

        try:
            result = self.requirements_agent.analyze_requirements(
                requirements_text=requirements_text,
            )

            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, "CUSTOMER REQUIREMENTS ANALYSIS\n")
            self.output_text.insert(tk.END, "=" * 70 + "\n\n")
            self.output_text.insert(tk.END, json.dumps(result, indent=4))

            if result.get("status") == "error":
                messagebox.showwarning(
                    "Analysis Failed",
                    result.get("message", "Requirements analysis failed."),
                )
            else:
                messagebox.showinfo(
                    "Analysis Complete",
                    "Customer requirements analysis completed successfully.",
                )

        except Exception as error:
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, "Requirements analysis failed:\n\n")
            self.output_text.insert(tk.END, str(error))
            messagebox.showerror("Requirements Analysis Error", str(error))

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


if __name__ == "__main__":
    root = tk.Tk()
    app = ModulaIntegrationApp(root)
    root.mainloop()