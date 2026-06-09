"""
desktop_app.py

Desktop interface for the Modula WMS Data Integration Agent.

Main flows:
1. Upload any accepted source
2. AI detects whether it is customer data or API documentation
3. Data files are mapped, packaged, processed, and converted to Modula XML
4. API documentation is analyzed for REST integration planning
5. SQL / ODBC connection strings are analyzed for future database integrations
"""

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog

from agents.api_documentation_analyzer import analyze_api_documentation_file
from agents.full_ai_onboarding_runner import run_full_ai_onboarding
from agents.sql_connection_analyzer import analyze_sql_connection_string
from src.connectors.source_detector import SourceDetector
from src.profiles.profile_registry import ProfileRegistry


class ModulaIntegrationApp:
    """
    Desktop application for AI-powered customer onboarding.
    """

    API_DOC_EXTENSIONS = {".txt", ".md", ".yaml", ".yml"}

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Modula WMS Agentic AI Integration Builder")
        self.root.geometry("950x740")

        self.profile_registry = ProfileRegistry()

        self._build_ui()

    def _build_ui(self):
        title = tk.Label(
            self.root,
            text="Modula WMS Agentic AI Integration Builder",
            font=("Arial", 18, "bold"),
        )
        title.pack(pady=15)

        description = tk.Label(
            self.root,
            text=(
                "Upload a customer data file or API documentation. "
                "The AI agent detects the source, analyzes the schema, maps fields "
                "to Modula WMS, generates an integration package, and converts "
                "supported data files into Modula XML."
            ),
            font=("Arial", 10),
            wraplength=850,
            justify="center",
        )
        description.pack(pady=5)

        upload_button = tk.Button(
            self.root,
            text="Upload Source and Build Integration",
            command=self.upload_source_and_build_integration,
            width=55,
            height=2,
        )
        upload_button.pack(pady=10)

        sql_button = tk.Button(
            self.root,
            text="Analyze SQL / ODBC Connection",
            command=self.analyze_sql_connection,
            width=55,
            height=2,
        )
        sql_button.pack(pady=5)

        profiles_button = tk.Button(
            self.root,
            text="View Registered Customer Profiles",
            command=self.open_profile_manager,
            width=55,
        )
        profiles_button.pack(pady=5)

        self.output_text = tk.Text(
            self.root,
            height=28,
            width=110,
        )
        self.output_text.pack(pady=15)

    def upload_source_and_build_integration(self):
        file_path = filedialog.askopenfilename(
            title="Upload Customer Source or API Documentation",
            filetypes=[
                (
                    "Supported Sources",
                    "*.csv *.json *.xml *.txt *.md *.yaml *.yml",
                ),
                ("Data Files", "*.csv *.json *.xml"),
                ("API Documentation", "*.txt *.md *.json *.yaml *.yml"),
                ("All Files", "*.*"),
            ],
        )

        if not file_path:
            return

        detected_type = self.detect_source_kind(file_path)

        if detected_type == "api_documentation":
            self.run_api_documentation_flow(file_path)
            return

        if detected_type in ["csv", "json", "xml"]:
            self.run_data_file_flow(file_path, detected_type)
            return

        messagebox.showwarning(
            "Unsupported Source",
            f"Unsupported or unknown source type:\n{file_path}",
        )

    def detect_source_kind(self, file_path: str) -> str:
        suffix = Path(file_path).suffix.lower()

        if suffix in self.API_DOC_EXTENSIONS:
            return "api_documentation"

        if suffix == ".json" and self.is_openapi_json(file_path):
            return "api_documentation"

        return SourceDetector.detect_source_type(file_path)

    def is_openapi_json(self, file_path: str) -> bool:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, dict):
                return False

            return (
                "openapi" in data
                or "swagger" in data
                or "paths" in data
            )

        except Exception:
            return False

    def run_data_file_flow(self, file_path: str, source_type: str):
        customer_name = simpledialog.askstring(
            "Customer Name",
            "Enter customer name:",
            parent=self.root,
        )

        if not customer_name:
            messagebox.showwarning(
                "Missing Customer Name",
                "Customer name is required for data-file integrations.",
            )
            return

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, "Detected customer data file.\n")
        self.output_text.insert(
            tk.END,
            "Running Agentic AI integration workflow...\n\n",
        )
        self.output_text.insert(tk.END, f"Customer: {customer_name}\n")
        self.output_text.insert(tk.END, f"Source File: {file_path}\n")
        self.output_text.insert(tk.END, f"Detected Source Type: {source_type}\n\n")

        try:
            result = run_full_ai_onboarding(
                customer_name=customer_name,
                source_type=source_type,
                file_path=file_path,
            )

            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(
                tk.END,
                "AGENTIC AI DATA INTEGRATION PACKAGE COMPLETE\n",
            )
            self.output_text.insert(tk.END, "=" * 70 + "\n\n")

            self.output_text.insert(
                tk.END,
                f"Customer: {result.get('customer_name')}\n",
            )
            self.output_text.insert(
                tk.END,
                f"Source Type: {result.get('source_type')}\n",
            )
            self.output_text.insert(
                tk.END,
                f"Integration Folder: {result.get('integration_folder')}\n",
            )
            self.output_text.insert(
                tk.END,
                f"Converted XML: {result.get('converted_xml_path')}\n",
            )
            self.output_text.insert(
                tk.END,
                f"Processing Result: {result.get('processing_result_path')}\n\n",
            )

            self.output_text.insert(tk.END, "Full Result:\n")
            self.output_text.insert(tk.END, json.dumps(result, indent=4))

            messagebox.showinfo(
                "Integration Complete",
                (
                    f"Integration package generated for {customer_name}.\n\n"
                    f"Folder:\n{result.get('integration_folder')}"
                ),
            )

        except Exception as error:
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(
                tk.END,
                "Integration generation failed:\n\n",
            )
            self.output_text.insert(tk.END, str(error))

            messagebox.showerror(
                "Integration Error",
                str(error),
            )

    def run_api_documentation_flow(self, file_path: str):
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, "Detected API documentation.\n")
        self.output_text.insert(
            tk.END,
            "Running AI API documentation analysis...\n\n",
        )
        self.output_text.insert(tk.END, f"API Documentation File: {file_path}\n\n")

        try:
            result = analyze_api_documentation_file(file_path)

            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(
                tk.END,
                "API DOCUMENTATION ANALYSIS COMPLETE\n",
            )
            self.output_text.insert(tk.END, "=" * 70 + "\n\n")
            self.output_text.insert(
                tk.END,
                f"Output Path: {result.get('output_path')}\n\n",
            )
            self.output_text.insert(tk.END, "Full Result:\n")
            self.output_text.insert(tk.END, json.dumps(result, indent=4))

            messagebox.showinfo(
                "API Analysis Complete",
                (
                    "API documentation analysis complete.\n\n"
                    f"Output:\n{result.get('output_path')}"
                ),
            )

        except Exception as error:
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(
                tk.END,
                "API documentation analysis failed:\n\n",
            )
            self.output_text.insert(tk.END, str(error))

            messagebox.showerror(
                "API Analysis Error",
                str(error),
            )

    def analyze_sql_connection(self):
        connection_string = simpledialog.askstring(
            "SQL / ODBC Connection",
            "Enter SQL / ODBC connection string:",
            parent=self.root,
        )

        if not connection_string:
            return

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(
            tk.END,
            "Analyzing SQL / ODBC connection...\n\n",
        )

        try:
            result = analyze_sql_connection_string(connection_string)

            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(
                tk.END,
                "SQL / ODBC ANALYSIS COMPLETE\n",
            )
            self.output_text.insert(tk.END, "=" * 70 + "\n\n")
            self.output_text.insert(
                tk.END,
                f"Output Path: {result.get('output_path')}\n\n",
            )
            self.output_text.insert(tk.END, "Full Result:\n")
            self.output_text.insert(tk.END, json.dumps(result, indent=4))

            messagebox.showinfo(
                "SQL Analysis Complete",
                f"Output:\n{result.get('output_path')}",
            )

        except Exception as error:
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(
                tk.END,
                "SQL / ODBC analysis failed:\n\n",
            )
            self.output_text.insert(tk.END, str(error))

            messagebox.showerror(
                "SQL Analysis Error",
                str(error),
            )

    def open_profile_manager(self):
        profiles = self.profile_registry.get_profiles()

        profile_window = tk.Toplevel(self.root)
        profile_window.title("Registered Customer Profiles")
        profile_window.geometry("850x550")

        title = tk.Label(
            profile_window,
            text="Registered Customer Profiles",
            font=("Arial", 16, "bold"),
        )
        title.pack(pady=10)

        frame = tk.Frame(profile_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        profile_listbox = tk.Listbox(frame, width=30)
        profile_listbox.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        details_text = tk.Text(frame, width=80)
        details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for profile_name in profiles.keys():
            profile_listbox.insert(tk.END, profile_name)

        def show_profile_details(event):
            selection = profile_listbox.curselection()

            if not selection:
                return

            profile_name = profile_listbox.get(selection[0])
            profile = profiles.get(profile_name, {})

            details_text.delete("1.0", tk.END)
            details_text.insert(tk.END, f"Profile: {profile_name}\n")
            details_text.insert(tk.END, "=" * 60 + "\n\n")
            details_text.insert(tk.END, json.dumps(profile, indent=4))

        profile_listbox.bind(
            "<<ListboxSelect>>",
            show_profile_details,
        )