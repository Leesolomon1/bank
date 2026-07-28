import json
from copy import deepcopy
from pathlib import Path
from typing import Any


SETTINGS_PATH = Path(__file__).with_name("settings.json")

DEFAULT_SETTINGS = {
    "enabled": True,
    "read_deposit": True,
    "read_withdraw": False,
    "minimum_amount": 1000,
    "quiet_enabled": False,
    "quiet_start": "23:00",
    "quiet_end": "08:00",
}


def load_settings() -> dict[str, Any]:
    settings = deepcopy(DEFAULT_SETTINGS)

    if not SETTINGS_PATH.exists():
        save_settings(settings)
        return settings

    try:
        with SETTINGS_PATH.open("r", encoding="utf-8") as file:
            saved = json.load(file)

        if isinstance(saved, dict):
            settings.update(saved)

    except (OSError, json.JSONDecodeError):
        save_settings(settings)

    return settings


def save_settings(settings: dict[str, Any]) -> None:
    with SETTINGS_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            settings,
            file,
            ensure_ascii=False,
            indent=2,
        )