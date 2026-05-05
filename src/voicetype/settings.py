import json
from pathlib import Path


SETTINGS_PATH = Path(__file__).with_name("settings.json")

DEFAULT_SETTINGS = {
    "model_size": "base",
    "hotkey": "ctrl+alt+space",
    "start_with_windows": False,
    "auto_paste": True,
    "theme": "System",
}


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return DEFAULT_SETTINGS.copy()

    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_SETTINGS.copy()

    merged = DEFAULT_SETTINGS.copy()
    merged.update({k: v for k, v in data.items() if k in DEFAULT_SETTINGS})
    return merged


def save_settings(settings: dict) -> None:
    payload = DEFAULT_SETTINGS.copy()
    payload.update(settings)
    SETTINGS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
