"""Registry of provider configuration surfaces."""

from __future__ import annotations

from collections.abc import Iterable

from tillm.surfaces_gui import JetBrainsOpenAILikeSurface, QoderSurface
from tillm.surfaces_terminal import (
    ClaudeSettingsSurface,
    CodexConfigSurface,
    OpencodeConfigSurface,
)
from tillm.surfaces_types import UnknownSurfaceError

_SURFACES = (
    ClaudeSettingsSurface(),
    CodexConfigSurface(),
    OpencodeConfigSurface(),
    JetBrainsOpenAILikeSurface(),
    QoderSurface(),
)

SURFACE_ALIASES = {
    "claude": ClaudeSettingsSurface.id,
    "codex": CodexConfigSurface.id,
    "opencode": OpencodeConfigSurface.id,
    "jetbrains": JetBrainsOpenAILikeSurface.id,
    "qoder": QoderSurface.id,
}


def normalize_surface_ids(names: Iterable[str] | None) -> frozenset[str] | None:
    if not names:
        return None
    known = {surface.id for surface in _SURFACES}
    resolved = set()
    for raw in names:
        token = (raw or "").strip().lower()
        token = SURFACE_ALIASES.get(token, token)
        if token not in known:
            options = ", ".join(sorted(known | set(SURFACE_ALIASES)))
            raise UnknownSurfaceError(f"unknown surface {raw!r} (known: {options})")
        resolved.add(token)
    return frozenset(resolved)


def iter_surfaces(*, level: str | None = None, only: frozenset[str] | None = None):
    for surface in _SURFACES:
        if level is not None and surface.level != level:
            continue
        if only is not None and surface.id not in only:
            continue
        yield surface
