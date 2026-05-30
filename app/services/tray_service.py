from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon, QWidget

from app.config import ICON_PATH
from app.models.audio_app import AudioApp, process_names_match
from app.services.logger_service import get_logger


class TrayService(QObject):
    open_requested = pyqtSignal()
    exit_requested = pyqtSignal()
    refresh_requested = pyqtSignal()
    intercept_toggled = pyqtSignal(bool)
    app_selected = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self._tray = QSystemTrayIcon(parent)
        self._tray.setToolTip("KnobMixer")
        if ICON_PATH.exists():
            self._tray.setIcon(QIcon(str(ICON_PATH)))

        self._menu = QMenu(parent)
        self._app_menu = QMenu("Выбрать приложение", self._menu)

        self._open_action = QAction("Открыть", self._menu)
        self._intercept_action = QAction("Перехват включён", self._menu)
        self._intercept_action.setCheckable(True)
        self._refresh_action = QAction("Обновить список приложений", self._menu)
        self._exit_action = QAction("Выход", self._menu)

        self._menu.addAction(self._open_action)
        self._menu.addAction(self._intercept_action)
        self._menu.addMenu(self._app_menu)
        self._menu.addAction(self._refresh_action)
        self._menu.addSeparator()
        self._menu.addAction(self._exit_action)

        self._tray.setContextMenu(self._menu)
        self._tray.activated.connect(self._on_activated)
        self._open_action.triggered.connect(self.open_requested.emit)
        self._intercept_action.toggled.connect(self.intercept_toggled.emit)
        self._refresh_action.triggered.connect(self.refresh_requested.emit)
        self._exit_action.triggered.connect(self.exit_requested.emit)

    def show(self) -> None:
        if QSystemTrayIcon.isSystemTrayAvailable():
            self._tray.show()
            self.logger.info("Tray icon shown")
        else:
            self.logger.error("System tray is not available")

    def hide(self) -> None:
        self._tray.hide()

    def set_intercept_enabled(self, enabled: bool) -> None:
        self._intercept_action.blockSignals(True)
        self._intercept_action.setChecked(enabled)
        self._intercept_action.setText("Перехват включён" if enabled else "Перехват выключен")
        self._intercept_action.blockSignals(False)

    def lock_intercept_enabled(self) -> None:
        self.set_intercept_enabled(True)
        self._intercept_action.setEnabled(False)

    def update_app_menu(self, apps: list[AudioApp], selected_process: str) -> None:
        self._app_menu.clear()
        if not apps:
            action = QAction("Нет активных аудиосессий", self._app_menu)
            action.setEnabled(False)
            self._app_menu.addAction(action)
            return

        for app in apps:
            action = QAction(app.process_name, self._app_menu)
            action.setCheckable(True)
            action.setChecked(process_names_match(app.process_name, selected_process))
            action.triggered.connect(lambda _checked=False, process=app.process_name: self.app_selected.emit(process))
            self._app_menu.addAction(action)

    def show_message(self, title: str, message: str) -> None:
        if self._tray.isVisible():
            self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 1200)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.open_requested.emit()
