from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import psutil

from app.models.audio_app import AudioApp, process_names_match
from app.services.logger_service import get_logger

try:
    import comtypes
    from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
except Exception as import_error:  # pragma: no cover - depends on Windows packages
    comtypes = None
    AudioUtilities = None
    ISimpleAudioVolume = None
    PYCaw_IMPORT_ERROR = import_error
else:
    PYCaw_IMPORT_ERROR = None


@dataclass(slots=True)
class _SessionRef:
    process_name: str
    pid: int | None
    volume: Any


class AudioService:
    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self._com_initialized = False
        self._session_ref_cache: list[_SessionRef] = []
        self._session_ref_cache_at = 0.0
        self._session_cache_ttl = 0.35
        self._last_logged_apps_key: tuple[str, ...] = ()
        if PYCaw_IMPORT_ERROR is not None:
            self.logger.error("pycaw/comtypes import failed: %s", PYCaw_IMPORT_ERROR)

    @property
    def available(self) -> bool:
        return PYCaw_IMPORT_ERROR is None

    def shutdown(self) -> None:
        if comtypes is not None and self._com_initialized:
            try:
                comtypes.CoUninitialize()
            except Exception:
                self.logger.debug("CoUninitialize failed", exc_info=True)
            self._com_initialized = False

    def list_audio_apps(self) -> list[AudioApp]:
        if not self.available:
            self.logger.error("Cannot list audio sessions: pycaw is unavailable")
            return []

        grouped: dict[str, dict[str, Any]] = {}
        for session_ref in self._get_session_refs(refresh=True):
            key = session_ref.process_name.lower()
            item = grouped.setdefault(
                key,
                {
                    "process_name": session_ref.process_name,
                    "display_name": session_ref.process_name,
                    "pids": set(),
                    "volumes": [],
                    "muted": False,
                    "session_count": 0,
                },
            )
            if session_ref.pid:
                item["pids"].add(session_ref.pid)
            item["session_count"] += 1

            try:
                item["volumes"].append(float(session_ref.volume.GetMasterVolume()))
                item["muted"] = bool(item["muted"] or session_ref.volume.GetMute())
            except Exception:
                self.logger.debug("Failed to read session volume", exc_info=True)

        apps: list[AudioApp] = []
        for item in grouped.values():
            volumes = item["volumes"]
            average_volume = sum(volumes) / len(volumes) if volumes else None
            apps.append(
                AudioApp(
                    process_name=item["process_name"],
                    display_name=item["display_name"],
                    pids=sorted(item["pids"]),
                    session_count=item["session_count"],
                    volume=average_volume,
                    muted=item["muted"],
                )
            )

        apps.sort(key=lambda app: app.process_name.lower())
        apps_key = tuple(app.process_name for app in apps)
        if apps_key != self._last_logged_apps_key:
            self.logger.info("Found %d audio app(s): %s", len(apps), list(apps_key))
            self._last_logged_apps_key = apps_key
        return apps

    def has_sessions(self, process_name: str) -> bool:
        return bool(self._sessions_for_process(process_name))

    def get_app_volume(self, process_name: str) -> tuple[float, bool] | None:
        sessions = self._sessions_for_process(process_name)
        if not sessions:
            return None

        volumes: list[float] = []
        muted = False
        for session in sessions:
            try:
                volumes.append(float(session.volume.GetMasterVolume()))
                muted = muted or bool(session.volume.GetMute())
            except Exception:
                self.logger.debug("Failed to read volume for %s", process_name, exc_info=True)
        if not volumes:
            return None
        return sum(volumes) / len(volumes), muted

    def set_app_volume(self, process_name: str, volume: float) -> tuple[float, int] | None:
        sessions = self._sessions_for_process(process_name)
        if not sessions:
            self.logger.warning("Cannot set volume; process not found: %s", process_name)
            return None

        clamped = max(0.0, min(1.0, volume))
        changed = 0
        for session in sessions:
            try:
                session.volume.SetMasterVolume(clamped, None)
                changed += 1
            except Exception:
                self.logger.exception("Failed to set volume for %s pid=%s", process_name, session.pid)

        self.logger.info("Set %s volume to %.0f%% across %d session(s)", process_name, clamped * 100, changed)
        return clamped, changed

    def change_app_volume(self, process_name: str, delta: float) -> tuple[float, int] | None:
        current = self.get_app_volume(process_name)
        if current is None:
            return None
        new_volume = current[0] + delta
        return self.set_app_volume(process_name, new_volume)

    def set_app_mute(self, process_name: str, muted: bool) -> tuple[bool, int] | None:
        sessions = self._sessions_for_process(process_name)
        if not sessions:
            self.logger.warning("Cannot mute; process not found: %s", process_name)
            return None

        changed = 0
        for session in sessions:
            try:
                session.volume.SetMute(1 if muted else 0, None)
                changed += 1
            except Exception:
                self.logger.exception("Failed to set mute for %s pid=%s", process_name, session.pid)

        self.logger.info("Set %s mute=%s across %d session(s)", process_name, muted, changed)
        return muted, changed

    def toggle_app_mute(self, process_name: str) -> tuple[bool, int] | None:
        current = self.get_app_volume(process_name)
        if current is None:
            return None
        return self.set_app_mute(process_name, not current[1])

    def find_priority_target(self, priorities: list[str]) -> str | None:
        session_refs = self._get_session_refs()
        for priority in priorities:
            for session_ref in session_refs:
                if process_names_match(session_ref.process_name, priority):
                    return session_ref.process_name
        return None

    def get_foreground_audio_process(self) -> str | None:
        try:
            import win32gui
            import win32process

            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if not pid:
                return None
            process_name = psutil.Process(pid).name()
        except Exception:
            self.logger.debug("Failed to resolve foreground process", exc_info=True)
            return None

        if self.has_sessions(process_name):
            return process_name
        return None

    def _sessions_for_process(self, process_name: str) -> list[_SessionRef]:
        if not self.available or not process_name:
            return []

        refs = [
            session_ref
            for session_ref in self._get_session_refs()
            if process_names_match(session_ref.process_name, process_name)
        ]
        if refs:
            return refs

        return [
            session_ref
            for session_ref in self._get_session_refs(refresh=True)
            if process_names_match(session_ref.process_name, process_name)
        ]

    def _get_session_refs(self, refresh: bool = False) -> list[_SessionRef]:
        if not self.available:
            return []

        now = time.monotonic()
        if not refresh and now - self._session_ref_cache_at <= self._session_cache_ttl:
            return list(self._session_ref_cache)

        refs: list[_SessionRef] = []
        for session in self._safe_get_sessions():
            session_ref = self._session_to_ref(session)
            if session_ref is not None:
                refs.append(session_ref)

        self._session_ref_cache = refs
        self._session_ref_cache_at = now
        return list(refs)

    def _safe_get_sessions(self) -> list[Any]:
        self._ensure_com()
        try:
            return list(AudioUtilities.GetAllSessions())
        except Exception:
            self.logger.exception("Failed to query Windows audio sessions")
            return []

    def _ensure_com(self) -> None:
        if comtypes is None or self._com_initialized:
            return
        try:
            comtypes.CoInitialize()
            self._com_initialized = True
        except Exception:
            self.logger.debug("COM initialization failed or was already initialized", exc_info=True)

    def _session_to_ref(self, session: Any) -> _SessionRef | None:
        try:
            process = session.Process
            if process is None:
                return None

            process_name = process.name()
            pid = process.pid
            volume = session._ctl.QueryInterface(ISimpleAudioVolume)
            return _SessionRef(process_name=process_name, pid=pid, volume=volume)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
        except Exception:
            self.logger.debug("Failed to inspect audio session", exc_info=True)
            return None
