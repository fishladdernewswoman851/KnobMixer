from __future__ import annotations

import sys
import traceback

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from app.config import APP_NAME, ICON_PATH, ensure_runtime_dirs
from app.services.audio_service import AudioService
from app.services.autostart_service import AutostartService
from app.services.keyboard_hook_service import KeyboardHookService
from app.services.logger_service import get_logger, setup_logging
from app.services.raw_input_service import RawInputService
from app.services.settings_service import SettingsService
from app.ui.main_window import MainWindow


def main() -> int:
    ensure_runtime_dirs()
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Starting %s", APP_NAME)

    def log_unhandled_exception(exc_type, exc_value, exc_traceback):
        logger.critical(
            "Unhandled exception:\n%s",
            "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
        )

    sys.excepthook = log_unhandled_exception

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)

    if ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(ICON_PATH)))

    settings = SettingsService()
    audio_service = AudioService()
    keyboard_service = KeyboardHookService()
    raw_input_service = RawInputService()
    autostart_service = AutostartService()

    window = MainWindow(
        settings=settings,
        audio_service=audio_service,
        keyboard_service=keyboard_service,
        raw_input_service=raw_input_service,
        autostart_service=autostart_service,
    )

    if not settings.get_bool("launch_to_tray"):
        window.show()

    exit_code = app.exec()

    keyboard_service.stop()
    raw_input_service.stop()
    audio_service.shutdown()
    logger.info("Stopped %s", APP_NAME)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
