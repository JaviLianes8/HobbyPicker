"""Dialog helpers for HobbyPicker."""
import tkinter as tk
from tkinter import messagebox
from ..translations import tr


def show_error(root: tk.Tk, key: str) -> None:
    """Show an error message translated by key."""
    messagebox.showerror(tr("error"), tr(key))
