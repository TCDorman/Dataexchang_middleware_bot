"""
watch.py

Starts the Modula folder watcher.
"""

from src.automation.folder_watcher import FolderWatcher


watcher = FolderWatcher()

watcher.start()