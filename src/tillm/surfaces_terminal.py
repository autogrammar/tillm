"""Terminal client provider configuration surfaces."""

from __future__ import annotations

import os
from pathlib import Path

from tillm.providers import ProviderSpec
from tillm.surfaces_io import as_dict, provider_slug, read_json, same_url, write_private_json
from tillm.surfaces_types import SurfaceState


class ClaudeSettingsSurface:
    """``~/.claude/settings.json`` env block for manually launched claude-code."""

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
        data = read_json(path)
        env = as_dict(data.get("env"))
        configured = same_url(env.get("ANTHROPIC_BASE_URL"), spec.anthropic_base_url)
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
        env = as_dict(read_json(self._path()).get("env"))
        if same_url(env.get("ANTHROPIC_BASE_URL"), spec.anthropic_base_url):
            return str(env.get("ANTHROPIC_AUTH_TOKEN") or "").strip() or None
        return None

    def write(self, spec: ProviderSpec, token: str, model: str | None) -> Path:
        path = self._path()
        data = read_json(path)
        env = as_dict(data.get("env"))
        env["ANTHROPIC_BASE_URL"] = spec.anthropic_base_url
        env["ANTHROPIC_AUTH_TOKEN"] = token
        if model:
            env["ANTHROPIC_MODEL"] = model
        data["env"] = env
        write_private_json(path, data)
        return path


class CodexConfigSurface:
    """``~/.codex/config.toml`` model_providers table."""

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
        tables = as_dict(data.get("model_providers"))
        configured = any(
            isinstance(entry, dict)
            and same_url(entry.get("base_url"), spec.openai_base_url)
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
            detail=(
                f"token via env {spec.token_env}; select with "
                f"`codex -c model_provider={provider_slug(spec)}`"
            ),
        )

    def read_token(self, spec: ProviderSpec) -> str | None:
        return os.environ.get(spec.token_env, "").strip() or None

    def write(self, spec: ProviderSpec, token: str, model: str | None) -> Path:
        path = self._path()
        if self.read(spec).configured:
            return path
        slug = provider_slug(spec)
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
    """opencode JSON config with custom provider entry."""

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
        providers = as_dict(read_json(self._path()).get("provider"))
        for entry in providers.values():
            if not isinstance(entry, dict):
                continue
            options = as_dict(entry.get("options"))
            if same_url(options.get("baseURL"), spec.openai_base_url):
                return entry
        return {}

    def read(self, spec: ProviderSpec) -> SurfaceState:
        path = self._path()
        entry = self._entry(spec)
        options = as_dict(entry.get("options"))
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
        options = as_dict(self._entry(spec).get("options"))
        token = str(options.get("apiKey") or "").strip()
        return token if token and not token.startswith("{env:") else None

    def write(self, spec: ProviderSpec, token: str, model: str | None) -> Path:
        path = self._path()
        data = read_json(path)
        providers = as_dict(data.get("provider"))
        slug = provider_slug(spec)
        entry = as_dict(providers.get(slug))
        options = as_dict(entry.get("options"))
        options.update({"baseURL": spec.openai_base_url, "apiKey": token})
        entry["options"] = options
        if model:
            models = as_dict(entry.get("models"))
            models.setdefault(model, {})
            entry["models"] = models
        providers[slug] = entry
        data["provider"] = providers
        write_private_json(path, data)
        return path
