"""Provider config *surfaces*: everywhere on this machine a provider lives.

A surface is one tool's configuration location that can point at an LLM API
provider — terminal clients (claude-code settings, codex config, opencode
config) and GUI IDEs (JetBrains AI Assistant "OpenAI-like" provider, Qoder).
``tillm provider sync`` reconciles them against the tillm token store, which
stays the single source of truth:

- **import**: the store has no token but a surface does → copy it into the
  store (``providers.json``, chmod 600),
- **export**: the store has a token and a writable surface is missing or
  stale → write base URL + token into that surface,
- **manual**: GUI surfaces that keep secrets in an OS keychain are
  detect-only; the report says what to do (or what gillm should drive).

Clients spawned by ``tillm drive`` never need any of this — they get the
provider via the env overlay. Surfaces exist for tools launched *outside*
tillm: a bare ``claude`` in a terminal, an IDE started from the desktop.
"""

from __future__ import annotations

import json
import os
import re
import stat
from dataclasses import asdict, dataclass
from pathlib import Path

from tillm.providers import (
    ProviderSpec,
    get_provider_spec,
    provider_default_model,
    resolve_provider_token,
    save_provider_token,
)

LEVELS = ("terminal", "gui")


@dataclass(frozen=True)
class SurfaceState:
    surface_id: str
    level: str  # "terminal" | "gui"
    label: str
    path: str | None  # config file consulted; None when nothing exists yet
    present: bool  # a config file exists at all
    configured: bool  # it already points at this provider
    has_token: bool  # a token for this provider is readable from it
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


def _provider_slug(spec: ProviderSpec) -> str:
    return re.sub(r"[^a-z0-9]+", "", spec.id.lower())


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _write_private_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)  # may hold a token


def _same_url(a: str | None, b: str | None) -> bool:
    return bool(a) and bool(b) and a.rstrip("/") == b.rstrip("/")


# --------------------------------------------------------------------------
# Terminal surfaces
# --------------------------------------------------------------------------


class ClaudeSettingsSurface:
    """`~/.claude/settings.json` ``env`` block — a manually launched
    claude-code follows ``ANTHROPIC_BASE_URL``/``ANTHROPIC_AUTH_TOKEN``."""

    id = "claude-settings"
    level = "terminal"
    label = "Claude Code (~/.claude/settings.json)"
    writable = True
    export_warning = (
        "repoints EVERY manually launched `claude` at this provider "
        "(the Anthropic subscription stops being the default)"
    )

    def _path(self) -> Path:
        return Path.home() / ".claude" / "settings.json"

    def applicable(self, spec: ProviderSpec) -> bool:
        return bool(spec.anthropic_base_url)

    def read(self, spec: ProviderSpec) -> SurfaceState:
        path = self._path()
        data = _read_json(path)
        env = _dict(data.get("env"))
        configured = _same_url(env.get("ANTHROPIC_BASE_URL"), spec.anthropic_base_url)
        token = str(env.get("ANTHROPIC_AUTH_TOKEN") or "").strip() if configured else ""
        return SurfaceState(
            surface_id=self.id,
            level=self.level,
            label=self.label,
            path=str(path) if path.exists() else None,
            present=path.exists(),
            configured=configured,
            has_token=bool(token),
            model=str(env.get("ANTHROPIC_MODEL") or "").strip() or None,
            writable=self.writable,
        )

    def read_token(self, spec: ProviderSpec) -> str | None:
        env = _dict(_read_json(self._path()).get("env"))
        if _same_url(
            env.get("ANTHROPIC_BASE_URL"), spec.anthropic_base_url
        ):
            return str(env.get("ANTHROPIC_AUTH_TOKEN") or "").strip() or None
        return None

    def write(self, spec: ProviderSpec, token: str, model: str | None) -> Path:
        path = self._path()
        data = _read_json(path)
        env = _dict(data.get("env"))
        env["ANTHROPIC_BASE_URL"] = spec.anthropic_base_url
        env["ANTHROPIC_AUTH_TOKEN"] = token
        if model:
            env["ANTHROPIC_MODEL"] = model
        data["env"] = env
        _write_private_json(path, data)
        return path


class CodexConfigSurface:
    """`~/.codex/config.toml` ``model_providers`` table — codex reads the
    token from the provider's ``env_key`` environment variable."""

    id = "codex-config"
    level = "terminal"
    label = "Codex (~/.codex/config.toml)"
    writable = True

    def _path(self) -> Path:
        return Path.home() / ".codex" / "config.toml"

    def applicable(self, spec: ProviderSpec) -> bool:
        return bool(spec.openai_base_url)

    def _load(self) -> dict:
        import tomllib

        try:
            return tomllib.loads(self._path().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def read(self, spec: ProviderSpec) -> SurfaceState:
        path = self._path()
        data = self._load()
        tables = _dict(data.get("model_providers"))
        configured = any(
            isinstance(entry, dict)
            and _same_url(entry.get("base_url"), spec.openai_base_url)
            for entry in tables.values()
        )
        return SurfaceState(
            surface_id=self.id,
            level=self.level,
            label=self.label,
            path=str(path) if path.exists() else None,
            present=path.exists(),
            configured=configured,
            has_token=bool(os.environ.get(spec.token_env, "").strip()),
            model=None,
            writable=self.writable,
            detail=f"token via env {spec.token_env}; select with `codex -c model_provider={_provider_slug(spec)}`",
        )

    def read_token(self, spec: ProviderSpec) -> str | None:
        return os.environ.get(spec.token_env, "").strip() or None

    def write(self, spec: ProviderSpec, token: str, model: str | None) -> Path:
        path = self._path()
        if self.read(spec).configured:
            return path
        slug = _provider_slug(spec)
        block = (
            f"\n[model_providers.{slug}]\n"
            f'name = "{spec.label}"\n'
            f'base_url = "{spec.openai_base_url}"\n'
            f'env_key = "{spec.token_env}"\n'
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        path.write_text(existing + block, encoding="utf-8")
        return path


class OpencodeConfigSurface:
    """opencode JSON config — a custom ``provider`` entry with baseURL/apiKey."""

    id = "opencode-config"
    level = "terminal"
    label = "opencode (~/.config/opencode/opencode.json)"
    writable = True

    def _candidates(self) -> tuple[Path, ...]:
        return (
            Path.home() / ".config" / "opencode" / "opencode.json",
            Path.home() / ".config" / "opencode" / "config.json",
            Path.home() / ".opencode" / "opencode.json",
        )

    def _path(self) -> Path:
        for candidate in self._candidates():
            if candidate.exists():
                return candidate
        return self._candidates()[0]

    def applicable(self, spec: ProviderSpec) -> bool:
        return bool(spec.openai_base_url)

    def _entry(self, spec: ProviderSpec) -> dict:
        providers = _dict(_read_json(self._path()).get("provider"))
        for entry in providers.values():
            if not isinstance(entry, dict):
                continue
            options = _dict(entry.get("options"))
            if _same_url(
                options.get("baseURL"), spec.openai_base_url
            ):
                return entry
        return {}

    def read(self, spec: ProviderSpec) -> SurfaceState:
        path = self._path()
        entry = self._entry(spec)
        options = _dict(entry.get("options"))
        return SurfaceState(
            surface_id=self.id,
            level=self.level,
            label=self.label,
            path=str(path) if path.exists() else None,
            present=path.exists(),
            configured=bool(entry),
            has_token=bool(str(options.get("apiKey") or "").strip()),
            model=None,
            writable=self.writable,
        )

    def read_token(self, spec: ProviderSpec) -> str | None:
        options = _dict(self._entry(spec).get("options"))
        token = str(options.get("apiKey") or "").strip()
        return token if token and not token.startswith("{env:") else None

    def write(self, spec: ProviderSpec, token: str, model: str | None) -> Path:
        path = self._path()
        data = _read_json(path)
        providers = _dict(data.get("provider"))
        slug = _provider_slug(spec)
        entry = _dict(providers.get(slug))
        options = _dict(entry.get("options"))
        options.update({"baseURL": spec.openai_base_url, "apiKey": token})
        entry["options"] = options
        if model:
            models = _dict(entry.get("models"))
            models.setdefault(model, {})
            entry["models"] = models
        providers[slug] = entry
        data["provider"] = providers
        _write_private_json(path, data)
        return path


# --------------------------------------------------------------------------
# GUI surfaces (detect-only: secrets live in the IDE keychain)
# --------------------------------------------------------------------------


class JetBrainsOpenAILikeSurface:
    """JetBrains AI Assistant "OpenAI-like" provider XML. The base URL is in
    ``options/llm.provider.openai.like.xml``; the API key sits in the IDE
    PasswordSafe, so this surface only detects and reports."""

    id = "jetbrains-openai-like"
    level = "gui"
    label = "JetBrains IDE (AI Assistant, OpenAI-like)"
    writable = False

    def _paths(self) -> list[Path]:
        root = Path.home() / ".config" / "JetBrains"
        return sorted(root.glob("*/options/llm.provider.openai.like.xml"))

    def applicable(self, spec: ProviderSpec) -> bool:
        return bool(spec.openai_base_url)

    def read(self, spec: ProviderSpec) -> SurfaceState:
        import xml.etree.ElementTree as ET

        paths = self._paths()
        configured_path: Path | None = None
        for path in reversed(paths):  # newest IDE version wins
            try:
                tree = ET.parse(path)
            except (OSError, ET.ParseError):
                continue
            for option in tree.iter("option"):
                if option.get("name") == "baseUrl" and _same_url(
                    option.get("value"), spec.openai_base_url
                ):
                    configured_path = path
                    break
            if configured_path:
                break
        shown = configured_path or (paths[-1] if paths else None)
        return SurfaceState(
            surface_id=self.id,
            level=self.level,
            label=self.label,
            path=str(shown) if shown else None,
            present=bool(paths),
            configured=bool(configured_path),
            has_token=False,
            model=None,
            writable=self.writable,
            detail="API key lives in the IDE keychain — paste it once in "
            "Settings → AI Assistant → Models, or let gillm drive the dialog",
        )

    def read_token(self, spec: ProviderSpec) -> str | None:
        return None


class QoderSurface:
    """Qoder (JetBrains plugin) BYOK settings — detect-only."""

    id = "qoder"
    level = "gui"
    label = "Qoder (BYOK)"
    writable = False

    def _paths(self) -> list[Path]:
        root = Path.home() / ".config" / "JetBrains"
        return sorted(root.glob("*/options/qoder_setting.xml"))

    def applicable(self, spec: ProviderSpec) -> bool:
        return bool(self._markers(spec))

    def _markers(self, spec: ProviderSpec) -> tuple[str, ...]:
        markers = [spec.id.lower(), *[alias.lower() for alias in spec.aliases]]
        for url in (spec.openai_base_url, spec.anthropic_base_url):
            if url:
                markers.append(url.split("//", 1)[-1].split("/", 1)[0].lower())
        return tuple(marker for marker in markers if len(marker) > 2)

    def read(self, spec: ProviderSpec) -> SurfaceState:
        paths = self._paths()
        configured_path: Path | None = None
        markers = self._markers(spec)
        for path in reversed(paths):
            raw = self._configured_text(path)
            if raw and any(marker in raw for marker in markers):
                configured_path = path
                break
        shown = configured_path or (paths[-1] if paths else None)
        return SurfaceState(
            surface_id=self.id,
            level=self.level,
            label=self.label,
            path=str(shown) if shown else None,
            present=bool(paths),
            configured=bool(configured_path),
            has_token=False,
            model=None,
            writable=self.writable,
            detail="configure the key in Qoder → Settings → Models (BYOK)",
        )

    @staticmethod
    def _configured_text(path: Path) -> str:
        """Text of the user's own Qoder settings, minus the cached BYOK
        *catalog* — that lists every provider Qoder knows about and would
        make everything look configured."""
        import xml.etree.ElementTree as ET

        try:
            tree = ET.parse(path)
        except (OSError, ET.ParseError):
            return ""
        parts: list[str] = []
        for option in tree.iter("option"):
            if option.get("name") == "cachedByokConfigJson":
                continue
            parts.append(option.get("value") or "")
        return " ".join(parts).lower()

    def read_token(self, spec: ProviderSpec) -> str | None:
        return None


_SURFACES = (
    ClaudeSettingsSurface(),
    CodexConfigSurface(),
    OpencodeConfigSurface(),
    JetBrainsOpenAILikeSurface(),
    QoderSurface(),
)


# Short aliases accepted by --surface (full ids work too).
SURFACE_ALIASES = {
    "claude": ClaudeSettingsSurface.id,
    "codex": CodexConfigSurface.id,
    "opencode": OpencodeConfigSurface.id,
    "jetbrains": JetBrainsOpenAILikeSurface.id,
    "qoder": QoderSurface.id,
}


class UnknownSurfaceError(ValueError):
    pass


def normalize_surface_ids(names) -> frozenset[str] | None:
    """Resolve user-supplied surface names/aliases; None means "all"."""
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


def iter_surfaces(*, level: str | None = None, only=None):
    for surface in _SURFACES:
        if level is not None and surface.level != level:
            continue
        if only is not None and surface.id not in only:
            continue
        yield surface


# --------------------------------------------------------------------------
# Sync engine
# --------------------------------------------------------------------------


def _surface_in_sync(surface, spec: ProviderSpec, store_token: str) -> bool:
    """A configured surface counts as in sync when its token matches the
    store. Surfaces without their own token file (codex reads the env var)
    are in sync as soon as the provider block exists."""
    own_token = surface.read_token(spec)
    if surface.id == CodexConfigSurface.id:
        return True
    return own_token == store_token


def plan_sync(
    provider_id: str, *, level: str | None = None, only=None
) -> dict:
    """Dry-run reconciliation of ``provider_id`` across surfaces.

    Returns ``{"provider", "store_token", "states", "steps"}`` where each
    step is what :func:`apply_sync` would do. Tokens never appear in the
    payload — only presence flags.
    """
    spec = get_provider_spec(provider_id)
    store_token = resolve_provider_token(spec.id)
    states: list[SurfaceState] = []
    steps: list[SyncStep] = []
    import_pending = store_token is None
    for surface in iter_surfaces(level=level, only=only):
        if not surface.applicable(spec):
            continue
        state = surface.read(spec)
        states.append(state)
        if import_pending and surface.read_token(spec):
            steps.append(
                SyncStep(surface.id, "import-token", f"copy token into tillm store from {state.path}")
            )
            import_pending = False
        elif not state.writable:
            steps.append(
                SyncStep(
                    surface.id,
                    "ok" if state.configured else "manual",
                    state.detail,
                )
            )
        elif store_token is None:
            steps.append(SyncStep(surface.id, "skip", "no token in store yet"))
        elif state.configured and _surface_in_sync(surface, spec, store_token):
            steps.append(SyncStep(surface.id, "ok"))
        else:
            warning = getattr(surface, "export_warning", "")
            detail = f"write base URL + token for {spec.id}"
            steps.append(
                SyncStep(surface.id, "export", f"{detail}; {warning}" if warning else detail)
            )
    return {
        "provider": spec.id,
        "store_token": store_token is not None,
        "states": [state.to_dict() for state in states],
        "steps": [step.to_dict() for step in steps],
    }


def sync_all(
    *, level: str | None = None, only=None, apply: bool = False
) -> dict:
    """Machine-wide matrix: run :func:`plan_sync` (or :func:`apply_sync`)
    for every registered provider that has at least one applicable surface.

    Providers without any token anywhere still appear — with their
    ``token_url`` — so the report doubles as a "what could I plug in" list.
    """
    from tillm.providers import iter_provider_specs

    runner = apply_sync if apply else plan_sync
    reports: list[dict] = []
    for spec in iter_provider_specs():
        report = runner(spec.id, level=level, only=only)
        relevant = report["store_token"] or any(
            state["present"] for state in report["states"]
        )
        if not report["states"] or not relevant:
            continue
        report["label"] = spec.label
        report["kind"] = spec.kind
        report["token_url"] = spec.token_url
        reports.append(report)
    return {"applied": apply, "level": level, "providers": reports}


def apply_sync(
    provider_id: str, *, level: str | None = None, only=None
) -> dict:
    """Execute :func:`plan_sync`: import a missing store token first, then
    export to every writable surface that is missing or stale. The import
    re-plans, so one run takes a surface token all the way out to the other
    surfaces."""
    spec = get_provider_spec(provider_id)
    surfaces = {surface.id: surface for surface in iter_surfaces(level=level, only=only)}
    plan = plan_sync(provider_id, level=level, only=only)
    import_result: dict | None = None
    for step in plan["steps"]:
        if step["action"] != "import-token":
            continue
        token = surfaces[step["surface_id"]].read_token(spec)
        if token:
            save_provider_token(spec.id, token)
            import_result = {**step, "done": True}
            plan = plan_sync(provider_id, level=level, only=only)  # exports now unblocked
        else:
            import_result = {**step, "done": False, "detail": "token vanished"}
        break
    results: list[dict] = [import_result] if import_result else []
    for step in plan["steps"]:
        if step["action"] == "import-token":
            continue
        if step["action"] != "export":
            results.append({**step, "done": step["action"] == "ok"})
            continue
        surface = surfaces[step["surface_id"]]
        token = resolve_provider_token(spec.id)
        write = getattr(surface, "write", None)
        if not token or write is None:
            results.append({**step, "done": False, "detail": "no token in store"})
            continue
        path = write(spec, token, provider_default_model(spec.id))
        results.append({**step, "done": True, "detail": f"wrote {path}"})
    plan["steps"] = results
    plan["states"] = [
        surfaces[state["surface_id"]].read(spec).to_dict() for state in plan["states"]
    ]
    plan["store_token"] = resolve_provider_token(spec.id) is not None
    return plan
