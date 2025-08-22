import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".hobbypicker.json"
DEFAULT_SETTINGS = {"language": "system", "theme": "system"}


def load_settings() -> dict[str, str]:
    data = DEFAULT_SETTINGS.copy()
    try:
        if CONFIG_PATH.exists():
            with CONFIG_PATH.open("r", encoding="utf-8") as fh:
                stored = json.load(fh)
            data.update({k: stored.get(k, v) for k, v in data.items()})
    except Exception:
        pass
    return data


def save_settings(settings: dict[str, str]) -> None:
    try:
        with CONFIG_PATH.open("w", encoding="utf-8") as fh:
            json.dump(settings, fh)
    except Exception:
        pass
