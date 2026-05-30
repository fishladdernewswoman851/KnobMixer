from __future__ import annotations

import ctypes
import threading
from ctypes import wintypes

from PyQt6.QtCore import QObject, pyqtSignal

from app.services.logger_service import get_logger

WH_KEYBOARD_LL = 13
HC_ACTION = 0
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
WM_QUIT = 0x0012

VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_K = 0x4B

KEY_ACTIONS = {
    VK_VOLUME_UP: "up",
    VK_VOLUME_DOWN: "down",
    VK_VOLUME_MUTE: "mute",
}


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", wintypes.WPARAM),
    ]


LowLevelKeyboardProc = ctypes.WINFUNCTYPE(
    wintypes.LPARAM,
    ctypes.c_int,
    wintypes.WPARAM,
    wintypes.LPARAM,
)

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

user32.SetWindowsHookExW.argtypes = [
    ctypes.c_int,
    LowLevelKeyboardProc,
    wintypes.HANDLE,
    wintypes.DWORD,
]
user32.SetWindowsHookExW.restype = wintypes.HANDLE
user32.CallNextHookEx.argtypes = [
    wintypes.HANDLE,
    ctypes.c_int,
    wintypes.WPARAM,
    wintypes.LPARAM,
]
user32.CallNextHookEx.restype = wintypes.LPARAM
user32.UnhookWindowsHookEx.argtypes = [wintypes.HANDLE]
user32.UnhookWindowsHookEx.restype = wintypes.BOOL
user32.GetMessageW.argtypes = [
    ctypes.POINTER(wintypes.MSG),
    wintypes.HWND,
    wintypes.UINT,
    wintypes.UINT,
]
user32.GetMessageW.restype = wintypes.BOOL
user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.PostThreadMessageW.argtypes = [
    wintypes.DWORD,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HANDLE
kernel32.GetCurrentThreadId.restype = wintypes.DWORD


class KeyboardHookService(QObject):
    volume_event = pyqtSignal(str, str)
    switch_requested = pyqtSignal()
    status_changed = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.logger = get_logger(__name__)
        self._thread: threading.Thread | None = None
        self._thread_id: int | None = None
        self._hook_id: int | None = None
        self._callback: LowLevelKeyboardProc | None = None
        self._running = False
        self._suppress_system_volume = True

    @property
    def running(self) -> bool:
        return self._running

    def start(self, suppress_system_volume: bool = True) -> None:
        if self._running:
            self._suppress_system_volume = suppress_system_volume
            return

        self._suppress_system_volume = suppress_system_volume
        self._running = True
        self._thread = threading.Thread(target=self._run, name="KnobMixerKeyboardHook", daemon=True)
        self._thread.start()
        self.logger.info("Keyboard hook thread started")

    def stop(self) -> None:
        if not self._running:
            return

        self._running = False
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None
        self._thread_id = None
        self.logger.info("Keyboard hook stopped")

    def _run(self) -> None:
        self._thread_id = int(kernel32.GetCurrentThreadId())
        self._callback = LowLevelKeyboardProc(self._handle_keyboard_event)

        module_handle = kernel32.GetModuleHandleW(None)
        self._hook_id = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._callback, module_handle, 0)
        if not self._hook_id:
            error_code = ctypes.get_last_error()
            message = f"Failed to install keyboard hook, WinError={error_code}"
            self.logger.error(message)
            self.error.emit(message)
            self._running = False
            return

        self.status_changed.emit("Keyboard Hook активен")
        self.logger.info("Keyboard hook installed")

        message = wintypes.MSG()
        try:
            while self._running:
                result = user32.GetMessageW(ctypes.byref(message), None, 0, 0)
                if result == 0:
                    break
                if result == -1:
                    self.logger.error("GetMessageW failed in keyboard hook")
                    break
                user32.TranslateMessage(ctypes.byref(message))
                user32.DispatchMessageW(ctypes.byref(message))
        except Exception:
            self.logger.exception("Keyboard hook loop failed")
            self.error.emit("Ошибка Keyboard Hook")
        finally:
            if self._hook_id:
                user32.UnhookWindowsHookEx(self._hook_id)
                self._hook_id = None
            self._callback = None
            self._running = False
            self.status_changed.emit("Keyboard Hook остановлен")

    def _handle_keyboard_event(self, n_code: int, w_param: int, l_param: int) -> int:
        try:
            if n_code == HC_ACTION and w_param in (WM_KEYDOWN, WM_SYSKEYDOWN):
                event = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                action = KEY_ACTIONS.get(int(event.vkCode))
                if action:
                    self.logger.debug("Volume key captured: %s", action)
                    self.volume_event.emit(action, "keyboard_hook")
                    if self._suppress_system_volume:
                        return 1

                if int(event.vkCode) == VK_K and self._ctrl_alt_pressed():
                    self.switch_requested.emit()
        except Exception:
            self.logger.exception("Keyboard hook callback failed")

        return user32.CallNextHookEx(self._hook_id, n_code, w_param, l_param)

    def _ctrl_alt_pressed(self) -> bool:
        ctrl = bool(user32.GetAsyncKeyState(VK_CONTROL) & 0x8000)
        alt = bool(user32.GetAsyncKeyState(VK_MENU) & 0x8000)
        return ctrl and alt
