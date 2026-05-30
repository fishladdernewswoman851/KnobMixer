from __future__ import annotations

import ctypes
import struct
import threading
import time
from ctypes import wintypes

from PyQt6.QtCore import QObject, pyqtSignal

from app.services.logger_service import get_logger

try:
    import win32api
    import win32con
    import win32gui
except Exception as import_error:  # pragma: no cover - Windows-only feature
    win32api = None
    win32con = None
    win32gui = None
    WIN32_IMPORT_ERROR = import_error
else:
    WIN32_IMPORT_ERROR = None


RID_INPUT = 0x10000003
RIM_TYPEHID = 2
RIDEV_INPUTSINK = 0x00000100
RIDEV_REMOVE = 0x00000001
WM_INPUT = 0x00FF

HID_USAGE_PAGE_CONSUMER = 0x0C
HID_USAGE_CONSUMER_CONTROL = 0x01

CONSUMER_USAGE_ACTIONS = {
    0x00E9: "up",
    0x00EA: "down",
    0x00E2: "mute",
}


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", wintypes.USHORT),
        ("usUsage", wintypes.USHORT),
        ("dwFlags", wintypes.DWORD),
        ("hwndTarget", wintypes.HWND),
    ]


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType", wintypes.DWORD),
        ("dwSize", wintypes.DWORD),
        ("hDevice", wintypes.HANDLE),
        ("wParam", wintypes.WPARAM),
    ]


user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.RegisterRawInputDevices.argtypes = [
    ctypes.POINTER(RAWINPUTDEVICE),
    wintypes.UINT,
    wintypes.UINT,
]
user32.RegisterRawInputDevices.restype = wintypes.BOOL
user32.GetRawInputData.argtypes = [
    wintypes.HANDLE,
    wintypes.UINT,
    wintypes.LPVOID,
    ctypes.POINTER(wintypes.UINT),
    wintypes.UINT,
]
user32.GetRawInputData.restype = wintypes.UINT


class RawInputService(QObject):
    volume_event = pyqtSignal(str, str)
    status_changed = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.logger = get_logger(__name__)
        self._thread: threading.Thread | None = None
        self._running = False
        self._hwnd: int | None = None
        self._last_action = ""
        self._last_action_time = 0.0

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> None:
        if self._running:
            return
        if WIN32_IMPORT_ERROR is not None:
            message = f"pywin32 is unavailable: {WIN32_IMPORT_ERROR}"
            self.logger.error(message)
            self.error.emit(message)
            return

        self._running = True
        self._thread = threading.Thread(target=self._run, name="KnobMixerRawInput", daemon=True)
        self._thread.start()
        self.logger.info("Raw Input thread started")

    def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._hwnd:
            try:
                win32gui.PostMessage(self._hwnd, win32con.WM_CLOSE, 0, 0)
            except Exception:
                self.logger.debug("Failed to post WM_CLOSE to Raw Input window", exc_info=True)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None
        self._hwnd = None
        self.logger.info("Raw Input stopped")

    def _run(self) -> None:
        try:
            window_class = self._register_window_class()
            self._hwnd = win32gui.CreateWindow(
                window_class,
                "KnobMixer Raw Input",
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                win32api.GetModuleHandle(None),
                None,
            )
            self._register_raw_input(self._hwnd)
            self.status_changed.emit("Raw Input / HID активен")
            self.logger.info("Raw Input registered")
            win32gui.PumpMessages()
        except Exception:
            self.logger.exception("Raw Input service failed")
            self.error.emit("Ошибка Raw Input / HID")
        finally:
            if self._hwnd:
                self._unregister_raw_input()
            self._running = False
            self.status_changed.emit("Raw Input / HID остановлен")

    def _register_window_class(self) -> str:
        class_name = "KnobMixerRawInputWindow"
        wnd_class = win32gui.WNDCLASS()
        wnd_class.hInstance = win32api.GetModuleHandle(None)
        wnd_class.lpszClassName = class_name
        wnd_class.lpfnWndProc = self._window_proc
        try:
            win32gui.RegisterClass(wnd_class)
        except win32gui.error:
            pass
        return class_name

    def _window_proc(self, hwnd: int, message: int, w_param: int, l_param: int) -> int:
        if message == WM_INPUT:
            self._handle_raw_input(l_param)
            return 0
        if message == win32con.WM_CLOSE:
            win32gui.DestroyWindow(hwnd)
            return 0
        if message == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0
        return win32gui.DefWindowProc(hwnd, message, w_param, l_param)

    def _register_raw_input(self, hwnd: int) -> None:
        device = RAWINPUTDEVICE(
            usUsagePage=HID_USAGE_PAGE_CONSUMER,
            usUsage=HID_USAGE_CONSUMER_CONTROL,
            dwFlags=RIDEV_INPUTSINK,
            hwndTarget=hwnd,
        )
        if not user32.RegisterRawInputDevices(
            ctypes.byref(device),
            1,
            ctypes.sizeof(RAWINPUTDEVICE),
        ):
            raise ctypes.WinError(ctypes.get_last_error())

    def _unregister_raw_input(self) -> None:
        device = RAWINPUTDEVICE(
            usUsagePage=HID_USAGE_PAGE_CONSUMER,
            usUsage=HID_USAGE_CONSUMER_CONTROL,
            dwFlags=RIDEV_REMOVE,
            hwndTarget=None,
        )
        user32.RegisterRawInputDevices(ctypes.byref(device), 1, ctypes.sizeof(RAWINPUTDEVICE))

    def _handle_raw_input(self, raw_input_handle: int) -> None:
        try:
            size = wintypes.UINT(0)
            header_size = ctypes.sizeof(RAWINPUTHEADER)
            user32.GetRawInputData(raw_input_handle, RID_INPUT, None, ctypes.byref(size), header_size)
            if size.value == 0:
                return

            buffer = ctypes.create_string_buffer(size.value)
            result = user32.GetRawInputData(
                raw_input_handle,
                RID_INPUT,
                buffer,
                ctypes.byref(size),
                header_size,
            )
            if result == wintypes.UINT(-1).value:
                self.logger.debug("GetRawInputData failed: %s", ctypes.get_last_error())
                return

            header = RAWINPUTHEADER.from_buffer_copy(buffer)
            if header.dwType != RIM_TYPEHID:
                return

            raw = buffer.raw[: size.value]
            hid_offset = ctypes.sizeof(RAWINPUTHEADER)
            if len(raw) < hid_offset + 8:
                return

            size_hid, count = struct.unpack_from("II", raw, hid_offset)
            data_offset = hid_offset + 8
            hid_data = raw[data_offset : data_offset + size_hid * count]
            action = self._decode_consumer_action(hid_data)
            if action:
                self._emit_action(action)
        except Exception:
            self.logger.exception("Failed to process Raw Input message")

    def _decode_consumer_action(self, data: bytes) -> str | None:
        if not data or all(byte == 0 for byte in data):
            return None

        for index in range(0, max(0, len(data) - 1)):
            usage = data[index] | (data[index + 1] << 8)
            action = CONSUMER_USAGE_ACTIONS.get(usage)
            if action:
                return action

        for byte in data:
            action = CONSUMER_USAGE_ACTIONS.get(byte)
            if action:
                return action
        return None

    def _emit_action(self, action: str) -> None:
        now = time.monotonic()
        if action == self._last_action and now - self._last_action_time < 0.08:
            return
        self._last_action = action
        self._last_action_time = now
        self.logger.debug("Raw Input volume event: %s", action)
        self.volume_event.emit(action, "raw_input")
