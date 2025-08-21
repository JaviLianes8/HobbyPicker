import tkinter as tk
from tkinter import ttk

from presentation.utils.window_utils import WindowUtils
from presentation.widgets.styles import apply_style


class SimpleEntryDialog:
    @staticmethod
    def ask(parent, title, prompt, initial_value=""):
        result = {"value": None}

        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.transient(parent)
        dialog.grab_set()
        dialog.resizable(False, False)
        WindowUtils.center_window(dialog, 600, 200)
        apply_style(dialog)

        ttk.Label(dialog, text=prompt, style="Heading.TLabel").pack(pady=10)
        entry = ttk.Entry(dialog, width=75)
        entry.insert(0, initial_value)
        entry.pack(pady=10)
        entry.focus()

        def on_ok():
            result["value"] = entry.get().strip()
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Aceptar", command=on_ok, style="Big.TButton").pack(
            side="left", padx=10
        )
        ttk.Button(button_frame, text="Cancelar", command=on_cancel, style="Big.TButton").pack(
            side="left", padx=10
        )

        dialog.wait_window()
        return result["value"]

