from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "KnobMixer"

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def appdata_dir() -> Path:
    base = os.environ.get("APPDATA")
    if base:
        return Path(base) / APP_NAME
    return Path.home() / f".{APP_NAME.lower()}"


DATA_DIR = appdata_dir() if is_frozen() else PROJECT_ROOT
SETTINGS_PATH = DATA_DIR / "settings.json"
LOG_DIR = DATA_DIR / "logs"
LOG_FILE = LOG_DIR / "app.log"

RESOURCE_ROOT = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))
ASSETS_DIR = RESOURCE_ROOT / "app" / "assets"
ICON_PATH = ASSETS_DIR / "icon.ico"


def ensure_runtime_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
