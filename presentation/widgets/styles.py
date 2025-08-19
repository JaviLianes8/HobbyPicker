"""Style helpers for Tkinter widgets with light and dark themes."""

from __future__ import annotations

from tkinter import ttk

try:  # Optional dependency; theme detection falls back gracefully
    import darkdetect
except Exception:  # pragma: no cover - best effort optional import
    darkdetect = None  # type: ignore

_CURRENT_THEME = "light"
_CURRENT_PALETTE: dict[str, str] = {}


def detect_system_theme() -> str:
    """Return ``'dark'`` if the OS is in dark mode, otherwise ``'light'``."""
    if darkdetect:
        try:
            return "dark" if darkdetect.isDark() else "light"
        except Exception:
            pass
    return "light"


def get_color(name: str) -> str:
    """Expose current palette colors to non-ttk widgets."""
    return _CURRENT_PALETTE.get(name, "")


def apply_style(master: ttk.Widget | None = None, theme: str | None = None) -> None:
    """Apply an accessible theme to the application.

    Parameters
    ----------
    master:
        Optional root widget to apply background colors to.
    theme:
        ``'light'``, ``'dark'`` or ``'system'`` to auto-detect. When ``None`` the
        previously selected theme is reused.
    """

    global _CURRENT_THEME, _CURRENT_PALETTE

    if theme is None:
        theme = _CURRENT_THEME
    if theme == "system":
        theme = detect_system_theme()
    _CURRENT_THEME = theme

    if theme == "dark":
        palette = {
            "primary": "#0A84FF",
            "primary_hover": "#0063B1",
            "background": "#1E1E1E",
            "surface": "#2C2C2C",
            "light": "#3A3A3A",
            "text": "#FFFFFF",
            "subtle": "#CCCCCC",
            "contrast": "#FFFFFF",
        }
    else:  # light theme
        palette = {
            "primary": "#0078D4",
            "primary_hover": "#0063B1",
            "background": "#F4F6F9",
            "surface": "#FFFFFF",
            "light": "#D1D9E0",
            "text": "#1F2A36",
            "subtle": "#6B7785",
            "contrast": "#000000",
        }

    _CURRENT_PALETTE = palette

    style = ttk.Style(master)
    style.theme_use("clam")

    primary = palette["primary"]
    primary_hover = palette["primary_hover"]
    background = palette["background"]
    surface = palette["surface"]
    light = palette["light"]
    text = palette["text"]
    subtle = palette["subtle"]
    contrast = palette["contrast"]

    base_font = ("Helvetica", 11)
    bold_font = ("Helvetica", 11, "bold")
    large_font = ("Helvetica", 13, "bold")

    style.configure(".", background=background, foreground=text, font=base_font)
    style.configure("TFrame", background=background)
    surface_border = 0 if theme == "dark" else 1
    surface_relief = "flat" if theme == "dark" else "ridge"
    style.configure(
        "Surface.TFrame",
        background=surface,
        relief=surface_relief,
        borderwidth=surface_border,
    )
    style.configure(
        "Outlined.Surface.TFrame",
        background=surface,
        bordercolor=contrast,
        borderwidth=1,
        relief="solid",
    )
    style.configure("TLabel", background=background, font=base_font, foreground=text)
    style.configure(
        "Surface.TLabel", background=surface, font=base_font, foreground=text
    )
    style.configure("Heading.TLabel", font=large_font)
    style.configure(
        "Heading.Surface.TLabel",
        background=surface,
        font=large_font,
        foreground=text,
    )
    style.configure("TEntry", relief="flat", padding=6, foreground="black")
    style.map("TEntry", foreground=[("focus", "black")])

    style.configure("TNotebook", background=background, padding=10)
    style.configure(
        "TNotebook.Tab",
        background=surface,
        foreground=subtle,
        font=bold_font,
        padding=(12, 6),
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", background)],
        foreground=[("selected", primary)],
    )

    style.configure(
        "TButton",
        background=primary,
        foreground="white",
        font=bold_font,
        padding=8,
        relief="flat",
        borderwidth=0,
    )
    style.map(
        "TButton",
        background=[("active", primary_hover), ("disabled", light)],
        relief=[("pressed", "sunken")],
    )
    style.configure("Big.TButton", font=large_font, padding=(12, 10))

    style.configure("TCombobox", fieldbackground=surface, background=light, padding=6)

    style.configure("TRadiobutton", background=background, padding=5)
    style.configure("TCheckbutton", background=background, padding=5)

    scroll_conf = dict(
        gripcount=0,
        background=light,
        darkcolor=light,
        lightcolor=light,
        troughcolor=background,
        bordercolor=light,
        arrowcolor=primary,
    )
    style.configure("Vertical.TScrollbar", **scroll_conf)
    style.configure("Horizontal.TScrollbar", **scroll_conf)

    style.configure("Toplevel", background=background)

    if master is not None:
        master.configure(bg=background)

    tree_border = 0 if theme == "dark" else 1
    style.configure(
        "Probability.Treeview",
        background=surface,
        fieldbackground=surface,
        foreground=text,
        bordercolor=light,
        borderwidth=tree_border,
        rowheight=24,
    )
    style.map(
        "Probability.Treeview",
        background=[("selected", primary)],
    )
    style.configure(
        "Probability.Treeview.Heading",
        background=light,
        foreground=text,
        font=bold_font,
        relief="flat",
        borderwidth=0,
    )

