"""Style helpers for Tkinter widgets with light and dark themes."""

from __future__ import annotations

from tkinter import ttk, font, TclError

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

    # --- Color palette ---
    # Adopt a calmer palette inspired by modern design systems for a more
    # professional look.  Both light and dark themes share the same accent color
    # for consistent branding.
    if theme == "dark":
        palette = {
            "primary": "#1E88E5",
            "primary_hover": "#1565C0",
            "background": "#0D0D0D",
            "surface": "#1A1A1A",
            "light": "#2E2E2E",
            "text": "#F0F0F0",
            "subtle": "#B0BEC5",
            "contrast": "#FFFFFF",
        }
    else:  # light theme
        palette = {
            "primary": "#1E88E5",
            "primary_hover": "#1565C0",
            "background": "#E8EAED",
            "surface": "#FFFFFF",
            "light": "#CFD8DC",
            "text": "#1C1C1C",
            "subtle": "#5F6A6A",
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

    # Use a system font that looks crisp on most platforms.  Segoe UI is present
    # on Windows and falls back gracefully elsewhere.
    base_font = ("Segoe UI", 11)
    bold_font = ("Segoe UI", 11, "bold")
    large_font = ("Segoe UI", 13, "bold")

    style.configure(".", background=background, foreground=text, font=base_font)
    style.configure("TFrame", background=background)
    surface_border = 0
    surface_relief = "flat"
    style.configure(
        "Surface.TFrame",
        background=surface,
        relief=surface_relief,
        borderwidth=surface_border,
    )
    style.configure(
        "Outlined.Surface.TFrame",
        background=surface,
        bordercolor=light,
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
    # Title labels are used for the global header
    title_font = ("Segoe UI", 16, "bold")
    style.configure("Title.TLabel", font=title_font, background=background, foreground=text)
    style.configure(
        "Title.Surface.TLabel",
        font=title_font,
        background=surface,
        foreground=text,
    )
    style.configure(
        "TEntry",
        relief="flat",
        padding=6,
        foreground=text,
        fieldbackground=surface,
        background=surface,
        insertcolor=contrast,
    )
    style.map("TEntry", foreground=[("focus", contrast)])

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
    style.map(
        "TCheckbutton",
        background=[("disabled", background)],
        foreground=[("disabled", text)],
    )

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
        columnseparatorcolor=light,
        rowseparatorcolor=light,
        columnseparatorwidth=1,
        rowseparatorwidth=1,
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


def add_button_hover(button: ttk.Button) -> None:
    """Apply a subtle hover animation to a ttk.Button."""
    style_name = button.cget("style") or "TButton"
    style = ttk.Style(button)
    base_font = style.lookup(style_name, "font") or button.cget("font")

    # ``font.nametofont`` only accepts named fonts.  On some platforms ttk styles
    # store fonts as tuples, which would raise a ``TclError``.  Fall back to
    # constructing a ``Font`` object manually in that case.
    try:
        f = font.nametofont(base_font)
    except Exception:  # pragma: no cover - platform dependent
        f = font.Font(font=base_font)

    hover_font = f.copy()
    hover_font.configure(size=f.cget("size") + 1)

    supports_font = "font" in button.keys()
    # ttk style names use a ``prefix.Class`` structure.  Appending ``.hover``
    # would make ``hover`` the widget class, which breaks inheritance and
    # results in "layout not found" errors on some platforms (e.g. when the
    # style is ``Big.TButton``).  Prepending the prefix keeps the original
    # class and lets the new style inherit from the base one correctly.
    hover_style = f"hover.{style_name}"
    # Always configure the hover style so it exists if we later fall back to
    # ``button.configure(style=hover_style)``.  Without this Tk may raise a
    # ``layout not found`` error on platforms that don't support direct font
    # configuration.
    style.configure(hover_style, font=hover_font)

    def on_enter(_event):
        if supports_font:
            try:
                button.configure(font=hover_font)
            except TclError:
                button.configure(style=hover_style)
        else:
            button.configure(style=hover_style)

    def on_leave(_event):
        if supports_font:
            try:
                button.configure(font=f)
            except TclError:
                button.configure(style=style_name)
        else:
            button.configure(style=style_name)

    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)
