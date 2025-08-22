"""Persistence of application settings."""
import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".hobbypicker.json"


def load_settings() -> dict[str, str]:
    """Load saved UI settings."""
    data = {"language": "system", "theme": "system"}
    try:
        if CONFIG_PATH.exists():
            with CONFIG_PATH.open("r", encoding="utf-8") as fh:
                stored = json.load(fh)
            data.update({k: stored.get(k, v) for k, v in data.items()})
    except Exception:
        pass
    return data


def save_settings(language: str, theme: str) -> None:
    """Persist the given language and theme values."""
    try:
        with CONFIG_PATH.open("w", encoding="utf-8") as fh:
            json.dump({"language": language, "theme": theme}, fh)
    except Exception:
        pass
