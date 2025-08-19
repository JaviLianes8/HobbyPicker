from __future__ import annotations

import json
from pathlib import Path

PREFS_FILE = Path.home() / ".hobbypicker_prefs.json"


def load_theme() -> str:
    """Return the saved theme name or ``'system'`` if not set."""
    try:
        data = json.loads(PREFS_FILE.read_text())
        theme = data.get("theme", "system")
        if theme in {"light", "dark", "system"}:
            return theme
    except Exception:
        pass
    return "system"


def save_theme(theme: str) -> None:
    """Persist the chosen theme for the current user."""
    try:
        PREFS_FILE.write_text(json.dumps({"theme": theme}))
    except Exception:
        pass
