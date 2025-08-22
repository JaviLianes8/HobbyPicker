"""Entry point for the graphical application."""
import tkinter as tk

from presentation.widgets.styles import apply_style
from presentation.utils.window_utils import WindowUtils
from .settings import load_settings, save_settings
from .ui_components.tabs import build_tabs


def start_app() -> None:
    """Launch the main HobbyPicker window."""
    root = tk.Tk()
    root.state("zoomed")
    WindowUtils.center_window(root, 1240, 600)
    root.title("HobbyPicker")
    root.minsize(1240, 600)

    settings = load_settings()
    lang_var = tk.StringVar(value=settings["language"])
    theme_var = tk.StringVar(value=settings["theme"])
    apply_style(root, theme_var.get())

    refresh = build_tabs(root, lang_var)

    def on_lang(*_):
        refresh()
        save_settings(lang_var.get(), theme_var.get())

    def on_theme(*_):
        apply_style(root, theme_var.get())
        save_settings(lang_var.get(), theme_var.get())

    lang_var.trace_add("write", on_lang)
    theme_var.trace_add("write", on_theme)
    root.mainloop()
