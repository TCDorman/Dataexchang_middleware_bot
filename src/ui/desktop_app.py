"""
desktop_app.py

Desktop interface for the Modula WMS Data Integration Agent.

Features:
1. Select and process customer CSV files
2. View processing results
3. Open generated XML files
4. View customer profile mappings
"""

import json
import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from src.pipeline.file_processing_pipeline import FileProcessingPipeline
from src.profiles.profile_registry import ProfileRegistry


class ModulaIntegrationApp:
    """
    Desktop application for processing customer files.
    """

    def __init__(self, root: tk.Tk):
        """
        Initialize the desktop application.
        """

        self.root = root
        self.root.title("Modula WMS Data Integration Agent")
        self.root.geometry("850x600")

        self.selected_file = None
        self.latest_output_path = None

        self.pipeline = FileProcessingPipeline()
        self.profile_registry = ProfileRegistry()

        self._build_ui()

    def _build_ui(self):
        """
        Build the main application UI.
        """

        title = tk.Label(
            self.root,
            text="Modula WMS Data Integration Agent",
            font=("Arial", 18, "bold"),
        )
        title.pack(pady=15)

        self.file_label = tk.Label(
            self.root,
            text="No file selected",
            font=("Arial", 10),
        )
        self.file_label.pack(pady=5)

        select_button = tk.Button(
            self.root,
            text="Select Customer CSV File",
            command=self.select_file,
            width=30,
        )
        select_button.pack(pady=5)

        process_button = tk.Button(
            self.root,
            text="Process File",
            command=self.process_file,
            width=30,
        )
        process_button.pack(pady=5)

        self.open_xml_button = tk.Button(
            self.root,
            text="Open Generated XML",
            command=self.open_generated_xml,
            width=30,
            state=tk.DISABLED,
        )
        self.open_xml_button.pack(pady=5)

        profiles_button = tk.Button(
            self.root,
            text="View Customer Profiles",
            command=self.open_profile_manager,
            width=30,
        )
        profiles_button.pack(pady=5)

        self.output_text = tk.Text(
            self.root,
            height=20,
            width=95,
        )
        self.output_text.pack(pady=15)

    def select_file(self):
        """
        Let the user select a CSV file.
        """

        file_path = filedialog.askopenfilename(
            title="Select Customer CSV File",
            filetypes=[
                ("CSV Files", "*.csv"),
                ("All Files", "*.*"),
            ],
        )

        if file_path:
            self.selected_file = file_path
            self.latest_output_path = None
            self.open_xml_button.config(state=tk.DISABLED)

            self.file_label.config(
                text=f"Selected: {Path(file_path).name}"
            )

    def process_file(self):
        """
        Process the selected CSV file.
        """

        if not self.selected_file:
            messagebox.showwarning(
                "No File Selected",
                "Please select a CSV file first.",
            )
            return

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, "Processing file...\n\n")

        result = self.pipeline.process_file(self.selected_file)

        export_result = result.get("export_result", {})
        output_path = export_result.get("output_path")

        if output_path:
            self.latest_output_path = output_path
            self.open_xml_button.config(state=tk.NORMAL)
        else:
            self.latest_output_path = None
            self.open_xml_button.config(state=tk.DISABLED)

        self._display_result(result)

    def open_generated_xml(self):
        """
        Open the latest generated XML file.
        """

        if not self.latest_output_path:
            messagebox.showwarning(
                "No XML File",
                "No generated XML file is available to open.",
            )
            return

        output_path = Path(self.latest_output_path)

        if not output_path.exists():
            messagebox.showerror(
                "File Not Found",
                f"Could not find XML file:\n{output_path}",
            )
            return

        os.startfile(output_path)

    def open_profile_manager(self):
        """
        Open a profile manager window.
        """

        profiles = self.profile_registry.get_profiles()

        profile_window = tk.Toplevel(self.root)
        profile_window.title("Customer Profiles")
        profile_window.geometry("850x550")

        title = tk.Label(
            profile_window,
            text="Customer Profiles",
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
            """
            Display the selected profile JSON.
            """

            selection = profile_listbox.curselection()

            if not selection:
                return

            profile_name = profile_listbox.get(selection[0])
            profile = profiles.get(profile_name, {})

            details_text.delete("1.0", tk.END)
            details_text.insert(
                tk.END,
                f"Profile: {profile_name}\n",
            )
            details_text.insert(tk.END, "=" * 60 + "\n\n")
            details_text.insert(
                tk.END,
                json.dumps(profile, indent=4),
            )

        profile_listbox.bind(
            "<<ListboxSelect>>",
            show_profile_details,
        )

    def _display_result(self, result: dict):
        """
        Display processing results.
        """

        self.output_text.delete("1.0", tk.END)

        self.output_text.insert(
            tk.END,
            "MODULA WMS DATA INTEGRATION RESULT\n",
        )
        self.output_text.insert(tk.END, "=" * 60 + "\n\n")

        self.output_text.insert(
            tk.END,
            f"Status: {result.get('status')}\n",
        )
        self.output_text.insert(
            tk.END,
            f"Source File: {result.get('source_file')}\n",
        )
        self.output_text.insert(
            tk.END,
            f"Profile Used: {result.get('profile_used')}\n",
        )
        self.output_text.insert(
            tk.END,
            f"Parser Used: {result.get('parser_used')}\n",
        )
        self.output_text.insert(
            tk.END,
            f"Orders Loaded: {result.get('orders_loaded')}\n\n",
        )

        decision = result.get("decision", {})
        self.output_text.insert(tk.END, "Decision:\n")
        self.output_text.insert(
            tk.END,
            f"  Action: {decision.get('action')}\n",
        )
        self.output_text.insert(
            tk.END,
            f"  Reason: {decision.get('reason')}\n\n",
        )

        export_result = result.get("export_result", {})
        self.output_text.insert(tk.END, "Export:\n")
        self.output_text.insert(
            tk.END,
            f"  Status: {export_result.get('status')}\n",
        )
        self.output_text.insert(
            tk.END,
            f"  Output Path: {export_result.get('output_path')}\n",
        )
        self.output_text.insert(
            tk.END,
            f"  Orders Exported: {export_result.get('orders_exported')}\n\n",
        )

        if result.get("history_record"):
            history = result["history_record"]
            self.output_text.insert(tk.END, "History:\n")
            self.output_text.insert(
                tk.END,
                f"  Timestamp: {history.get('timestamp')}\n",
            )
            self.output_text.insert(
                tk.END,
                "  Transaction recorded successfully.\n\n",
            )

        if result.get("error_message"):
            self.output_text.insert(tk.END, "Error:\n")
            self.output_text.insert(
                tk.END,
                f"  {result.get('error_message')}\n",
            )