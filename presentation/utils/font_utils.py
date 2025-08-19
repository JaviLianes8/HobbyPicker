from tkinter import font


def safe_font(size: int = 12, weight: str = "normal") -> font.Font:
    """Return a font available on the current system.

    Tries a list of common families and falls back to TkDefaultFont
    to ensure consistent rendering across different environments.
    """
    for family in ("Segoe UI", "Helvetica", "Arial", "Liberation Sans"):
        if family in font.families():
            return font.Font(family=family, size=size, weight=weight)
    fallback = font.nametofont("TkDefaultFont").copy()
    fallback.configure(size=size, weight=weight)
    return fallback
