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


class ModulaIntegrationApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Modula WMS Agentic AI Integration Builder")
        self.root.geometry("950x750")

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
                "Use this tool to build Modula WMS integrations from customer files, "
                "REST API documentation, or SQL / ODBC sources."
            ),
            font=("Arial", 10),
            wraplength=850,
            justify="center",
        ).pack(pady=5)

        tk.Button(
            self.root,
            text="Upload File / REST API Documentation",
            command=self.upload_source_and_build_integration,
            width=55,
            height=2,
        ).pack(pady=10)

        tk.Button(
            self.root,
            text="SQL / ODBC Integration",
            command=self.run_sql_integration,
            width=55,
            height=2,
        ).pack(pady=5)

        self.output_text = tk.Text(self.root, height=30, width=110)
        self.output_text.pack(pady=15)

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