"""
desktop_app.py

Desktop interface for the Modula WMS Data Integration Agent.
"""

import json
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog

sys.path.append(str(Path(__file__).resolve().parents[2]))

from agents.integration_workflow_manager import IntegrationWorkflowManager
from src.profiles.profile_registry import ProfileRegistry


class ModulaIntegrationApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Modula WMS Agentic AI Integration Builder")
        self.root.geometry("950x820")

        self.profile_registry = ProfileRegistry()
        self.workflow_manager = IntegrationWorkflowManager()

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
                "Upload a customer data file or API documentation. "
                "The workflow manager routes the source to the correct agent."
            ),
            font=("Arial", 10),
            wraplength=850,
            justify="center",
        ).pack(pady=5)

        tk.Button(
            self.root,
            text="Upload Source and Build Integration",
            command=self.upload_source_and_build_integration,
            width=55,
            height=2,
        ).pack(pady=10)

        tk.Button(
            self.root,
            text="Run Demo Workflow",
            command=self.run_demo_workflow,
            width=55,
            height=2,
        ).pack(pady=5)

        tk.Button(
            self.root,
            text="Analyze SQL / ODBC Connection",
            command=self.analyze_sql_connection,
            width=55,
            height=2,
        ).pack(pady=5)

        tk.Button(
            self.root,
            text="Run Live SQL → Modula XML",
            command=self.run_live_sql_to_xml,
            width=55,
            height=2,
        ).pack(pady=5)

        tk.Button(
            self.root,
            text="View Registered Customer Profiles",
            command=self.open_profile_manager,
            width=55,
        ).pack(pady=5)

        self.output_text = tk.Text(self.root, height=28, width=110)
        self.output_text.pack(pady=15)

    def run_demo_workflow(self):
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, "Running demo workflow...\n\n")

        try:
            result = self.workflow_manager.run_demo_workflow()

            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, "DEMO WORKFLOW COMPLETE\n")
            self.output_text.insert(tk.END, "=" * 70 + "\n\n")
            self.output_text.insert(tk.END, json.dumps(result, indent=4))

            if result.get("status") == "success":
                messagebox.showinfo(
                    "Demo Workflow Complete",
                    "Demo workflow completed successfully.",
                )
            else:
                messagebox.showwarning(
                    "Demo Workflow Failed",
                    result.get("message", "Unknown demo workflow error."),
                )

        except Exception as error:
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, "Demo workflow failed:\n\n")
            self.output_text.insert(tk.END, str(error))
            messagebox.showerror("Demo Workflow Error", str(error))

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
        self.output_text.insert(tk.END, "Running workflow manager...\n\n")

        try:
            result = self.workflow_manager.run_file_workflow(
                file_path=file_path,
                customer_name=customer_name,
            )

            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, "WORKFLOW COMPLETE\n")
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

    def open_profile_manager(self):
        profiles = self.profile_registry.get_profiles()

        profile_window = tk.Toplevel(self.root)
        profile_window.title("Registered Customer Profiles")
        profile_window.geometry("850x550")

        tk.Label(
            profile_window,
            text="Registered Customer Profiles",
            font=("Arial", 16, "bold"),
        ).pack(pady=10)

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

        profile_listbox.bind("<<ListboxSelect>>", show_profile_details)


if __name__ == "__main__":
    root = tk.Tk()
    app = ModulaIntegrationApp(root)
    root.mainloop()