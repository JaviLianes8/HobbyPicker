"""Entry point for the graphical application."""
import tkinter as tk

from presentation.widgets.styles import apply_style
from .settings import load_settings, save_settings
from .translations import tr, get_effective_language
from .ui_components.tabs import build_tabs


def start_app() -> None:
    """Launch the main HobbyPicker window."""
    root = tk.Tk()
    root.state("zoomed")
    root.title("HobbyPicker")
    root.minsize(1240, 600)

    settings = load_settings()
    lang_var = tk.StringVar(value=settings["language"])
    theme_var = tk.StringVar(value=settings["theme"])
    apply_style(root, theme_var.get())

    # Build UI
    lang_code = get_effective_language(lang_var.get())
    build_tabs(root, lang_code)

    def persist(*_):
        save_settings(lang_var.get(), theme_var.get())
        apply_style(root, theme_var.get())

    lang_var.trace_add("write", persist)
    theme_var.trace_add("write", persist)
    root.mainloop()
