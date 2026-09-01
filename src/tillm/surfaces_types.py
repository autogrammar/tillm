"""Shared types for provider configuration surfaces."""

from __future__ import annotations

from dataclasses import asdict, dataclass

LEVELS = ("terminal", "gui")


@dataclass(frozen=True)
class SurfaceState:
    surface_id: str
    level: str  # "terminal" | "gui"
    label: str
    path: str | None
    present: bool
    configured: bool
    has_token: bool
    model: str | None
    writable: bool
    detail: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SyncStep:
    surface_id: str
    action: str  # "import-token" | "export" | "ok" | "manual" | "skip"
    detail: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class UnknownSurfaceError(ValueError):
    pass
