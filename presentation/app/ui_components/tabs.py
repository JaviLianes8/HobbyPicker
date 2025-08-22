"""Notebook tabs for the main window."""
import tkinter as tk
from tkinter import ttk
from ..translations import tr


def build_tabs(root: tk.Tk, lang_code: str) -> tuple[ttk.Frame, ttk.Frame]:
    """Create the main notebook with two simple tabs."""
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)
    today = ttk.Frame(notebook)
    config = ttk.Frame(notebook)
    notebook.add(today, text=tr("tab_today", lang_code))
    notebook.add(config, text=tr("tab_config", lang_code))
    return today, config
