"""Provider config *surfaces*: everywhere on this machine a provider lives.

See module doc in the original ``surfaces`` facade; submodules split by
responsibility (types, I/O, terminal/gui implementations, registry, sync).
"""

from tillm.surfaces_gui import JetBrainsOpenAILikeSurface, QoderSurface
from tillm.surfaces_registry import (
    SURFACE_ALIASES,
    iter_surfaces,
    normalize_surface_ids,
)
from tillm.surfaces_sync import apply_sync, plan_sync, sync_all
from tillm.surfaces_terminal import (
    ClaudeSettingsSurface,
    CodexConfigSurface,
    OpencodeConfigSurface,
)
from tillm.surfaces_types import LEVELS, SurfaceState, SyncStep, UnknownSurfaceError

__all__ = [
    "LEVELS",
    "ClaudeSettingsSurface",
    "CodexConfigSurface",
    "JetBrainsOpenAILikeSurface",
    "OpencodeConfigSurface",
    "QoderSurface",
    "SURFACE_ALIASES",
    "SurfaceState",
    "SyncStep",
    "UnknownSurfaceError",
    "apply_sync",
    "iter_surfaces",
    "normalize_surface_ids",
    "plan_sync",
    "sync_all",
]
