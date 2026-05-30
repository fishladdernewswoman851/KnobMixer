from __future__ import annotations

import sys
from pathlib import Path

from app.config import APP_NAME, PROJECT_ROOT, is_frozen
from app.services.logger_service import get_logger

try:
    import winreg
except ImportError:  # pragma: no cover - Windows-only feature
    winreg = None


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


class AutostartService:
    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    def is_enabled(self) -> bool:
        if winreg is None:
            return False
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as key:
                winreg.QueryValueEx(key, APP_NAME)
            return True
        except FileNotFoundError:
            return False
        except OSError:
            return False

    def set_enabled(self, enabled: bool) -> bool:
        if winreg is None:
            self.logger.error("winreg is not available; autostart cannot be changed")
            return False

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                RUN_KEY,
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                if enabled:
                    command = self._launch_command()
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
                    self.logger.info("Autostart enabled: %s", command)
                else:
                    try:
                        winreg.DeleteValue(key, APP_NAME)
                    except FileNotFoundError:
                        pass
                    self.logger.info("Autostart disabled")
            return True
        except Exception:
            self.logger.exception("Failed to change autostart state to %s", enabled)
            return False

    def _launch_command(self) -> str:
        if is_frozen():
            return f'"{Path(sys.executable)}"'

        python_exe = Path(sys.executable)
        pythonw = python_exe.with_name("pythonw.exe")
        if pythonw.exists():
            python_exe = pythonw
        main_path = PROJECT_ROOT / "main.py"
        return f'"{python_exe}" "{main_path}"'
