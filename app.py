"""
app.py

Launches the Modula WMS Data Integration Agent desktop app.
"""

import tkinter as tk

from src.ui.desktop_app import ModulaIntegrationApp
from agents.integration_package_generator import generate_integration_package

root = tk.Tk()
app = ModulaIntegrationApp(root)
root.mainloop()

if __name__ == "__main__":
    result = generate_integration_package("Ford", "csv")
    print(result)