"""Utilities related to font selection."""

from functools import lru_cache
from tkinter import font

_PREFERRED_FAMILIES = ("Segoe UI", "Helvetica", "Arial", "Liberation Sans")


def _choose_family() -> str:
    """Return the first available preferred family or the Tk default."""
    for family in _PREFERRED_FAMILIES:
        if family in font.families():
            return family
    return font.nametofont("TkDefaultFont").cget("family")


@lru_cache(maxsize=None)
def safe_font(size: int = 12, weight: str = "normal") -> font.Font:
    """Return a ``tkinter.font.Font`` that exists on the current system.

    The chosen family is cached so repeated calls avoid recomputing
    available font families.
    """
    family = _choose_family()
    return font.Font(family=family, size=size, weight=weight)
