from __future__ import annotations

import time

from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models.audio_app import AudioApp, process_names_match
from app.services.audio_service import AudioService
from app.services.autostart_service import AutostartService
from app.services.keyboard_hook_service import KeyboardHookService
from app.services.logger_service import get_logger
from app.services.raw_input_service import RawInputService
from app.services.settings_service import SettingsService
from app.services.tray_service import TrayService
from app.ui.styles import DARK_STYLE

HOOK_MODES = {
    "auto": "Авто",
    "keyboard": "Keyboard Hook",
    "raw_input": "Raw Input / HID",
}

TARGET_MODES = {
    "selected": "Выбранное приложение",
    "active": "Активное приложение со звуком",
    "priority": "Приоритет приложений",
}


class MainWindow(QMainWindow):
    def __init__(
        self,
        settings: SettingsService,
        audio_service: AudioService,
        keyboard_service: KeyboardHookService,
        raw_input_service: RawInputService,
        autostart_service: AutostartService,
    ) -> None:
        super().__init__()
        self.settings = settings
        self.audio_service = audio_service
        self.keyboard_service = keyboard_service
        self.raw_input_service = raw_input_service
        self.autostart_service = autostart_service
        self.logger = get_logger(__name__)

        self.apps: list[AudioApp] = []
        self._is_exiting = False
        self._last_event_action = ""
        self._last_event_time = 0.0
        self._last_notification_time = 0.0

        self.setWindowTitle("KnobMixer")
        self.resize(760, 620)
        self.setMinimumSize(700, 540)
        self.setStyleSheet(DARK_STYLE)

        self._build_ui()
        self.tray_service = TrayService(self)
        self._connect_signals()
        self._load_settings_into_ui()
        self.tray_service.lock_intercept_enabled()
        self.tray_service.show()

        self.refresh_sessions()
        self._apply_intercept_mode()

        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_target_status)
        self.status_timer.start(2500)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_sessions)
        self.refresh_timer.start(12000)

    def _build_ui(self) -> None:
        central = QWidget(self)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(12)

        title = QLabel("KnobMixer")
        title.setObjectName("TitleLabel")
        subtitle = QLabel("Управление громкостью выбранного приложения через клавиши, ручку или медиарегулятор")
        subtitle.setObjectName("StatusLabel")

        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(14)

        apps_group = QGroupBox("Активные приложения со звуком")
        apps_layout = QVBoxLayout(apps_group)
        self.apps_list = QListWidget()
        self.refresh_button = QPushButton("Обновить список")
        apps_layout.addWidget(self.apps_list, 1)
        apps_layout.addWidget(self.refresh_button)
        content_layout.addWidget(apps_group, 3)

        settings_group = QGroupBox("Настройки")
        form = QFormLayout(settings_group)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(9)

        self.selected_label = QLabel("Не выбрано")
        self.controlled_label = QLabel("Не выбрано")
        self.volume_label = QLabel("-")

        self.target_mode_combo = QComboBox()
        for value, label in TARGET_MODES.items():
            self.target_mode_combo.addItem(label, value)

        self.step_combo = QComboBox()
        for step in (1, 2, 5, 10):
            self.step_combo.addItem(f"{step}%", step)

        self.hook_mode_combo = QComboBox()
        for value, label in HOOK_MODES.items():
            self.hook_mode_combo.addItem(label, value)

        self.intercept_checkbox = QCheckBox("Включить перехват регулятора")
        self.autostart_checkbox = QCheckBox("Запускать вместе с Windows")
        self.launch_to_tray_checkbox = QCheckBox("Запускать сразу в трее")
        self.notifications_checkbox = QCheckBox("Показывать уведомления")
        self.priority_edit = QPlainTextEdit()
        self.priority_edit.setPlaceholderText("Spotify.exe\nDiscord.exe\nchrome.exe")
        self.priority_edit.setMaximumHeight(84)

        self.test_button = QPushButton("Проверить управление")
        self.status_label = QLabel("Готово")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setWordWrap(True)

        form.addRow("Выбранное приложение", self.selected_label)
        form.addRow("Управляется сейчас", self.controlled_label)
        form.addRow("Текущая громкость", self.volume_label)
        form.addRow("Режим управления", self.target_mode_combo)
        form.addRow("Шаг громкости", self.step_combo)
        form.addRow("Режим перехвата", self.hook_mode_combo)
        form.addRow("", self.intercept_checkbox)
        form.addRow("", self.autostart_checkbox)
        form.addRow("", self.launch_to_tray_checkbox)
        form.addRow("", self.notifications_checkbox)
        form.addRow("Приоритет", self.priority_edit)
        form.addRow("", self.test_button)
        form.addRow("Статус", self.status_label)

        content_layout.addWidget(settings_group, 4)
        root_layout.addLayout(content_layout, 1)
        self.setCentralWidget(central)

    def _connect_signals(self) -> None:
        self.refresh_button.clicked.connect(self.refresh_sessions)
        self.apps_list.itemSelectionChanged.connect(self._on_app_selection_changed)
        self.step_combo.currentIndexChanged.connect(self._save_volume_step)
        self.hook_mode_combo.currentIndexChanged.connect(self._save_hook_mode)
        self.target_mode_combo.currentIndexChanged.connect(self._save_target_mode)
        self.intercept_checkbox.toggled.connect(self._on_intercept_toggled)
        self.autostart_checkbox.toggled.connect(self._on_autostart_toggled)
        self.launch_to_tray_checkbox.toggled.connect(
            lambda value: self.settings.set("launch_to_tray", bool(value))
        )
        self.notifications_checkbox.toggled.connect(
            lambda value: self.settings.set("show_notifications", bool(value))
        )
        self.priority_edit.textChanged.connect(self._save_priorities)
        self.test_button.clicked.connect(lambda: self._perform_control("up", "test", require_intercept=False))

        self.keyboard_service.volume_event.connect(self.handle_volume_event)
        self.keyboard_service.switch_requested.connect(self.select_next_app)
        self.keyboard_service.status_changed.connect(self._set_status)
        self.keyboard_service.error.connect(self._set_status)
        self.raw_input_service.volume_event.connect(self.handle_volume_event)
        self.raw_input_service.status_changed.connect(self._set_status)
        self.raw_input_service.error.connect(self._set_status)

        self.tray_service.open_requested.connect(self.show_from_tray)
        self.tray_service.exit_requested.connect(self.exit_application)
        self.tray_service.refresh_requested.connect(self.refresh_sessions)
        self.tray_service.intercept_toggled.connect(self._on_tray_intercept_toggled)
        self.tray_service.app_selected.connect(self.select_app_by_process)

    def _load_settings_into_ui(self) -> None:
        self.settings.set("intercept_enabled", True)
        self.intercept_checkbox.setChecked(True)
        self.intercept_checkbox.setEnabled(False)
        self.autostart_checkbox.setChecked(self.autostart_service.is_enabled())
        self.launch_to_tray_checkbox.setChecked(self.settings.get_bool("launch_to_tray"))
        self.notifications_checkbox.setChecked(self.settings.get_bool("show_notifications", True))

        self._select_combo_data(self.step_combo, int(self.settings.get("volume_step", 5)))
        self._select_combo_data(self.hook_mode_combo, self.settings.get("hook_mode", "auto"))
        self._select_combo_data(self.target_mode_combo, self.settings.get("target_mode", "selected"))

        priorities = self.settings.get("priority_apps", [])
        self.priority_edit.setPlainText("\n".join(str(item) for item in priorities))
        self._update_selected_label()

    def refresh_sessions(self) -> None:
        self.apps = self.audio_service.list_audio_apps()
        selected_process = self.settings.get("selected_process", "")

        self.apps_list.blockSignals(True)
        self.apps_list.clear()
        for app in self.apps:
            item = QListWidgetItem(self._format_app_item(app))
            item.setData(Qt.ItemDataRole.UserRole, app.process_name)
            item.setToolTip(self._format_app_tooltip(app))
            self.apps_list.addItem(item)
            if process_names_match(app.process_name, selected_process):
                item.setSelected(True)
                self.apps_list.setCurrentItem(item)
        self.apps_list.blockSignals(False)

        self.tray_service.update_app_menu(self.apps, selected_process)
        self._update_selected_label()
        self.update_target_status()

    def update_target_status(self) -> None:
        target = self._resolve_target_process()
        self.controlled_label.setText(target or "Не выбрано")

        if not target:
            self.volume_label.setText("-")
            self._set_status("Выберите приложение или настройте режим приоритета")
            return

        volume = self.audio_service.get_app_volume(target)
        if volume is None:
            self.volume_label.setText("-")
            self._set_status(f"Приложение не найдено: {target}")
            return

        percent = round(volume[0] * 100)
        muted = " mute" if volume[1] else ""
        self.volume_label.setText(f"{percent}%{muted}")
        self._set_status("Перехват включён" if self.intercept_checkbox.isChecked() else "Перехват выключен")

    @pyqtSlot(str, str)
    def handle_volume_event(self, action: str, source: str) -> None:
        if not self.intercept_checkbox.isChecked():
            return

        now = time.monotonic()
        if action == self._last_event_action and now - self._last_event_time < 0.08:
            return
        self._last_event_action = action
        self._last_event_time = now

        self._perform_control(action, source, require_intercept=True)

    @pyqtSlot()
    def select_next_app(self) -> None:
        if not self.apps:
            self.refresh_sessions()
        if not self.apps:
            self._set_status("Нет активных аудиосессий для переключения")
            return

        current = self.settings.get("selected_process", "")
        next_index = 0
        for index, app in enumerate(self.apps):
            if process_names_match(app.process_name, current):
                next_index = (index + 1) % len(self.apps)
                break

        target = self.apps[next_index].process_name
        self.select_app_by_process(target)
        self._notify("KnobMixer", f"Выбрано: {target}")

    @pyqtSlot(str)
    def select_app_by_process(self, process_name: str) -> None:
        self.settings.set("selected_process", process_name)
        self.logger.info("Selected application: %s", process_name)
        self._select_combo_data(self.target_mode_combo, "selected")
        self.settings.set("target_mode", "selected")
        self._update_selected_label()

        self.apps_list.blockSignals(True)
        for row in range(self.apps_list.count()):
            item = self.apps_list.item(row)
            item.setSelected(process_names_match(item.data(Qt.ItemDataRole.UserRole), process_name))
            if item.isSelected():
                self.apps_list.setCurrentItem(item)
        self.apps_list.blockSignals(False)

        self.tray_service.update_app_menu(self.apps, process_name)
        self.update_target_status()

    def show_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def exit_application(self) -> None:
        self._is_exiting = True
        self.keyboard_service.stop()
        self.raw_input_service.stop()
        self.tray_service.hide()
        QApplication.quit()

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt override
        if self._is_exiting:
            event.accept()
            return
        event.ignore()
        self.hide()
        self._notify("KnobMixer", "Окно скрыто в трей")

    def _perform_control(self, action: str, source: str, require_intercept: bool) -> None:
        if require_intercept and not self.intercept_checkbox.isChecked():
            return

        target = self._resolve_target_process()
        if not target:
            self._set_status("Приложение не найдено")
            return

        step = int(self.settings.get("volume_step", 5)) / 100.0
        result = None
        if action == "up":
            result = self.audio_service.change_app_volume(target, step)
        elif action == "down":
            result = self.audio_service.change_app_volume(target, -step)
        elif action == "mute":
            mute_result = self.audio_service.toggle_app_mute(target)
            if mute_result is not None:
                muted, changed = mute_result
                self._set_status(f"{target}: {'mute' if muted else 'unmute'} ({changed} сесс.)")
                self.logger.info("Mute toggled from %s for %s", source, target)
                self._notify("KnobMixer", f"{target}: {'mute' if muted else 'unmute'}")
                self.update_target_status()
            else:
                self._set_status(f"Приложение не найдено: {target}")
            return

        if result is None:
            self._set_status(f"Приложение не найдено: {target}")
            return

        volume, changed = result
        percent = round(volume * 100)
        self._set_status(f"{target}: {percent}% ({changed} сесс.)")
        self.logger.info("Volume changed from %s for %s to %s%%", source, target, percent)
        self._notify("KnobMixer", f"{target}: {percent}%")
        self.update_target_status()

    def _resolve_target_process(self) -> str | None:
        mode = self.settings.get("target_mode", "selected")
        if mode == "active":
            active = self.audio_service.get_foreground_audio_process()
            if active:
                return active
        if mode == "priority":
            priority = self.audio_service.find_priority_target(self._priority_apps())
            if priority:
                return priority
        selected = self.settings.get("selected_process", "")
        return selected or None

    def _on_app_selection_changed(self) -> None:
        selected_items = self.apps_list.selectedItems()
        if not selected_items:
            return
        process_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
        self.select_app_by_process(process_name)

    def _on_intercept_toggled(self, enabled: bool) -> None:
        if not enabled:
            self.intercept_checkbox.blockSignals(True)
            self.intercept_checkbox.setChecked(True)
            self.intercept_checkbox.blockSignals(False)
            enabled = True

        self.settings.set("intercept_enabled", True)
        self.tray_service.set_intercept_enabled(True)
        self._apply_intercept_mode()
        self.update_target_status()

    def _on_tray_intercept_toggled(self, enabled: bool) -> None:
        if not enabled:
            self.tray_service.set_intercept_enabled(True)
        self._on_intercept_toggled(True)

    def _on_autostart_toggled(self, enabled: bool) -> None:
        if self.autostart_service.set_enabled(bool(enabled)):
            self.settings.set("autostart_enabled", bool(enabled))
        else:
            self.autostart_checkbox.blockSignals(True)
            self.autostart_checkbox.setChecked(not enabled)
            self.autostart_checkbox.blockSignals(False)

    def _save_volume_step(self) -> None:
        self.settings.set("volume_step", int(self.step_combo.currentData()))

    def _save_hook_mode(self) -> None:
        self.settings.set("hook_mode", self.hook_mode_combo.currentData())
        self._apply_intercept_mode()

    def _save_target_mode(self) -> None:
        self.settings.set("target_mode", self.target_mode_combo.currentData())
        self.update_target_status()

    def _save_priorities(self) -> None:
        self.settings.set("priority_apps", self._priority_apps())

    def _apply_intercept_mode(self) -> None:
        enabled = True
        mode = self.settings.get("hook_mode", "auto")
        suppress = bool(self.settings.get("suppress_system_volume", True))

        if not enabled:
            self.keyboard_service.stop()
            self.raw_input_service.stop()
            return

        if mode in ("auto", "keyboard"):
            self.keyboard_service.start(suppress_system_volume=suppress)
        else:
            self.keyboard_service.stop()

        if mode in ("auto", "raw_input"):
            self.raw_input_service.start()
        else:
            self.raw_input_service.stop()

    def _priority_apps(self) -> list[str]:
        return [
            line.strip()
            for line in self.priority_edit.toPlainText().splitlines()
            if line.strip()
        ]

    def _update_selected_label(self) -> None:
        selected = self.settings.get("selected_process", "")
        self.selected_label.setText(selected or "Не выбрано")
        if hasattr(self, "tray_service"):
            self.tray_service.set_intercept_enabled(self.intercept_checkbox.isChecked())

    def _set_status(self, message: str) -> None:
        self.status_label.setText(message)

    def _notify(self, title: str, message: str) -> None:
        if not self.settings.get_bool("show_notifications", True):
            return
        now = time.monotonic()
        if now - self._last_notification_time < 0.7:
            return
        self._last_notification_time = now
        self.tray_service.show_message(title, message)

    def _select_combo_data(self, combo: QComboBox, value) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _format_app_item(self, app: AudioApp) -> str:
        volume = f"{app.volume_percent}%" if app.volume_percent is not None else "-"
        muted = " muted" if app.muted else ""
        return f"{app.process_name}  |  {volume}{muted}  |  {app.session_count} сесс."

    def _format_app_tooltip(self, app: AudioApp) -> str:
        pids = ", ".join(str(pid) for pid in app.pids) if app.pids else "-"
        return f"Process: {app.process_name}\nPID: {pids}\nSessions: {app.session_count}"
