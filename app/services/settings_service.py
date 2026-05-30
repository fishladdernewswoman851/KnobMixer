from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from app.config import SETTINGS_PATH, ensure_runtime_dirs
from app.services.logger_service import get_logger

DEFAULT_SETTINGS: dict[str, Any] = {
    "selected_process": "",
    "volume_step": 5,
    "intercept_enabled": True,
    "autostart_enabled": False,
    "launch_to_tray": False,
    "show_notifications": True,
    "hook_mode": "auto",
    "target_mode": "selected",
    "priority_apps": [
        "Spotify.exe",
        "Discord.exe",
        "chrome.exe",
        "msedge.exe",
        "firefox.exe",
    ],
    "suppress_system_volume": True,
}

FORCED_SETTINGS: dict[str, Any] = {
    "intercept_enabled": True,
}


class SettingsService:
    def __init__(self, path: Path = SETTINGS_PATH) -> None:
        self.path = path
        self.logger = get_logger(__name__)
        self._settings = deepcopy(DEFAULT_SETTINGS)
        self.load()

    def load(self) -> dict[str, Any]:
        ensure_runtime_dirs()
        if not self.path.exists():
            self.save()
            return self._settings

        try:
            with self.path.open("r", encoding="utf-8") as file:
                loaded = json.load(file)
            if isinstance(loaded, dict):
                self._settings = self._merge_defaults(loaded)
        except Exception:
            self.logger.exception("Failed to load settings from %s", self.path)
            self._settings = deepcopy(DEFAULT_SETTINGS)
        self._settings.update(FORCED_SETTINGS)
        return self._settings

    def save(self) -> None:
        ensure_runtime_dirs()
        try:
            temporary_path = self.path.with_suffix(".tmp")
            with temporary_path.open("w", encoding="utf-8") as file:
                json.dump(self._settings, file, indent=2, ensure_ascii=False)
            temporary_path.replace(self.path)
        except Exception:
            self.logger.exception("Failed to save settings to %s", self.path)

    def all(self) -> dict[str, Any]:
        return deepcopy(self._settings)

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def get_bool(self, key: str, default: bool = False) -> bool:
        return bool(self._settings.get(key, default))

    def set(self, key: str, value: Any, save: bool = True) -> None:
        if key in FORCED_SETTINGS:
            value = FORCED_SETTINGS[key]
        self._settings[key] = value
        if save:
            self.save()

    def update(self, values: dict[str, Any], save: bool = True) -> None:
        self._settings.update(values)
        self._settings.update(FORCED_SETTINGS)
        if save:
            self.save()

    def _merge_defaults(self, loaded: dict[str, Any]) -> dict[str, Any]:
        merged = deepcopy(DEFAULT_SETTINGS)
        merged.update(loaded)
        merged.update(FORCED_SETTINGS)
        if not isinstance(merged.get("priority_apps"), list):
            merged["priority_apps"] = deepcopy(DEFAULT_SETTINGS["priority_apps"])
        return merged
