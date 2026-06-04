"""
app.py

Launches the Modula WMS Data Integration Agent desktop app.
"""

import tkinter as tk

from src.ui.desktop_app import ModulaIntegrationApp


root = tk.Tk()
app = ModulaIntegrationApp(root)
root.mainloop()