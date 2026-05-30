from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AudioApp:
    process_name: str
    display_name: str
    pids: list[int] = field(default_factory=list)
    session_count: int = 0
    volume: float | None = None
    muted: bool = False

    @property
    def key(self) -> str:
        return normalize_process_name(self.process_name)

    @property
    def volume_percent(self) -> int | None:
        if self.volume is None:
            return None
        return round(self.volume * 100)

    def label(self) -> str:
        parts = [self.display_name or self.process_name]
        if self.process_name and self.process_name.lower() != (self.display_name or "").lower():
            parts.append(f"({self.process_name})")
        if self.session_count:
            parts.append(f"- {self.session_count} session(s)")
        if self.volume_percent is not None:
            parts.append(f"- {self.volume_percent}%")
        if self.muted:
            parts.append("- muted")
        return " ".join(parts)


def normalize_process_name(process_name: str | None) -> str:
    value = (process_name or "").strip().lower()
    return value


def process_names_match(left: str | None, right: str | None) -> bool:
    left_norm = normalize_process_name(left)
    right_norm = normalize_process_name(right)
    if not left_norm or not right_norm:
        return False
    if left_norm == right_norm:
        return True
    if not left_norm.endswith(".exe"):
        left_norm = f"{left_norm}.exe"
    if not right_norm.endswith(".exe"):
        right_norm = f"{right_norm}.exe"
    return left_norm == right_norm
