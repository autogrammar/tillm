"""Registry of LLM API providers usable behind shell clients.

A *client* (claude-code, aider, …) is the tool tillm drives; a *provider*
is the API/subscription that serves the model behind it. The same
claude-code binary can talk to Anthropic (native subscription) or to any
Anthropic-protocol-compatible vendor such as z.ai by overriding the base
URL + auth token environment variables. This module owns:

- the provider registry (``iter_provider_specs``),
- secure token storage (``~/.config/tillm/providers.json``, chmod 600),
- the per-client environment overlay (``provider_env_overlay``),
- a cheap connectivity probe (``probe_provider``).

Token resolution precedence: explicit process env var > stored token.
"""

from __future__ import annotations

import json
import os
import stat
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

_ANTHROPIC_VERSION = "2023-06-01"

# Which wire protocol each registered client speaks (for provider overlays).
_CLIENT_PROTOCOLS: dict[str, str] = {
    "claude-code": "anthropic",
    "aider": "openai",
    "codex": "openai",
}


@dataclass(frozen=True)
class ProviderSpec:
    id: str
    label: str
    kind: str  # "api" | "subscription"
    token_env: str
    docs_url: str = ""
    # Base URLs per protocol; None means "native endpoint of that protocol".
    anthropic_base_url: str | None = None
    openai_base_url: str | None = None
    # Models to try, in order, when probing connectivity.
    probe_models: tuple[str, ...] = ()
    default_model: str | None = None
    aliases: tuple[str, ...] = ()
    notes: str = ""

    def protocols(self) -> tuple[str, ...]:
        out = []
        if self.anthropic_base_url is not None or self.id == "anthropic":
            out.append("anthropic")
        if self.openai_base_url is not None or self.id == "openai":
            out.append("openai")
        return tuple(out)

    def compatible_clients(self) -> tuple[str, ...]:
        protos = set(self.protocols())
        return tuple(
            client for client, proto in _CLIENT_PROTOCOLS.items() if proto in protos
        )


_PROVIDERS: tuple[ProviderSpec, ...] = (
    ProviderSpec(
        id="anthropic",
        label="Anthropic (Claude)",
        kind="subscription",
        token_env="ANTHROPIC_API_KEY",
        docs_url="https://docs.anthropic.com",
        anthropic_base_url=None,  # native
        notes="claude-code native; subscription login or ANTHROPIC_API_KEY.",
    ),
    ProviderSpec(
        id="z.ai",
        label="Z.ai (GLM)",
        kind="api",
        token_env="ZAI_API_KEY",
        docs_url="https://docs.z.ai",
        anthropic_base_url="https://api.z.ai/api/anthropic",
        openai_base_url="https://api.z.ai/api/coding/paas/v4",
        probe_models=("glm-4.7", "glm-4.6", "glm-4.5"),
        default_model="glm-4.7",
        aliases=("zai", "z-ai", "glm", "zhipu"),
        notes="GLM coding plan; Anthropic-compatible endpoint drives claude-code.",
    ),
    ProviderSpec(
        id="openrouter",
        label="OpenRouter",
        kind="api",
        token_env="OPENROUTER_API_KEY",
        docs_url="https://openrouter.ai/docs",
        openai_base_url="https://openrouter.ai/api/v1",
        aliases=("or",),
        notes="Multi-model gateway; OpenAI-compatible (aider/codex lane).",
    ),
    ProviderSpec(
        id="openai",
        label="OpenAI",
        kind="api",
        token_env="OPENAI_API_KEY",
        docs_url="https://platform.openai.com/docs",
        openai_base_url=None,  # native
        notes="codex/aider native endpoint.",
    ),
)


class UnknownProviderError(ValueError):
    pass


def normalize_provider_id(raw: str) -> str:
    token = (raw or "").strip().lower()
    for spec in _PROVIDERS:
        if token == spec.id or token in spec.aliases:
            return spec.id
    return token


def get_provider_spec(provider_id: str) -> ProviderSpec:
    normalized = normalize_provider_id(provider_id)
    for spec in _PROVIDERS:
        if spec.id == normalized:
            return spec
    known = ", ".join(s.id for s in _PROVIDERS)
    raise UnknownProviderError(f"unknown provider {provider_id!r} (known: {known})")


def iter_provider_specs() -> tuple[ProviderSpec, ...]:
    return _PROVIDERS


# --------------------------------------------------------------------------
# Token storage
# --------------------------------------------------------------------------


def _config_path() -> Path:
    base = os.environ.get("TILLM_CONFIG_DIR", "").strip()
    root = Path(base) if base else Path.home() / ".config" / "tillm"
    return root / "providers.json"


def _load_store() -> dict:
    path = _config_path()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _write_store(data: dict) -> Path:
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0600 — tokens live here
    return path


def save_provider_token(
    provider_id: str,
    token: str,
    *,
    model: str | None = None,
) -> Path:
    spec = get_provider_spec(provider_id)
    store = _load_store()
    entry = dict(store.get(spec.id) or {})
    entry["token"] = token.strip()
    if model:
        entry["model"] = model.strip()
    store[spec.id] = entry
    return _write_store(store)


def stored_provider_entry(provider_id: str) -> dict:
    spec = get_provider_spec(provider_id)
    entry = _load_store().get(spec.id)
    return dict(entry) if isinstance(entry, dict) else {}


def resolve_provider_token(provider_id: str) -> str | None:
    """Env var wins over the stored token."""
    spec = get_provider_spec(provider_id)
    env_token = os.environ.get(spec.token_env, "").strip()
    if env_token:
        return env_token
    stored = stored_provider_entry(provider_id).get("token", "")
    return stored.strip() or None


def provider_default_model(provider_id: str) -> str | None:
    stored = stored_provider_entry(provider_id).get("model", "")
    if stored.strip():
        return stored.strip()
    return get_provider_spec(provider_id).default_model


# --------------------------------------------------------------------------
# Environment overlay for driving a client through a provider
# --------------------------------------------------------------------------


def client_protocol(client_id: str) -> str | None:
    return _CLIENT_PROTOCOLS.get((client_id or "").strip().lower())


def provider_env_overlay(client_id: str, provider_id: str) -> dict[str, str]:
    """Env vars that point ``client_id`` at ``provider_id``.

    Raises ``UnknownProviderError`` for unknown providers and ``ValueError``
    when the client/provider protocols do not match or no token is available
    for an API provider.
    """
    spec = get_provider_spec(provider_id)
    protocol = client_protocol(client_id)
    if protocol is None:
        raise ValueError(
            f"client {client_id!r} has no provider protocol mapping; "
            f"providers work with: {', '.join(sorted(_CLIENT_PROTOCOLS))}"
        )
    if protocol not in spec.protocols():
        raise ValueError(
            f"provider {spec.id!r} does not speak the {protocol!r} protocol "
            f"required by client {client_id!r} "
            f"(compatible clients: {', '.join(spec.compatible_clients()) or 'none'})"
        )
    token = resolve_provider_token(spec.id)
    if not token and spec.kind == "api":
        raise ValueError(
            f"no token for provider {spec.id!r}: export {spec.token_env} "
            f"or run `tillm provider set {spec.id}`"
        )

    overlay: dict[str, str] = {}
    if protocol == "anthropic":
        if spec.anthropic_base_url:
            overlay["ANTHROPIC_BASE_URL"] = spec.anthropic_base_url
            # claude-code reads ANTHROPIC_AUTH_TOKEN for non-Anthropic gateways.
            overlay["ANTHROPIC_AUTH_TOKEN"] = token or ""
        elif token:
            overlay["ANTHROPIC_API_KEY"] = token
        model = provider_default_model(spec.id)
        if spec.anthropic_base_url and model:
            overlay.setdefault("ANTHROPIC_MODEL", model)
    else:  # openai protocol
        if token:
            overlay["OPENAI_API_KEY"] = token
        if spec.openai_base_url:
            # aider honours OPENAI_API_BASE; codex/openai SDKs honour OPENAI_BASE_URL.
            overlay["OPENAI_API_BASE"] = spec.openai_base_url
            overlay["OPENAI_BASE_URL"] = spec.openai_base_url
    return overlay


def resolve_request_provider(explicit: str | None = None) -> str | None:
    """Provider chosen for this drive: explicit arg > TILLM_PROVIDER env."""
    raw = (explicit or "").strip() or os.environ.get("TILLM_PROVIDER", "").strip()
    return normalize_provider_id(raw) if raw else None


# --------------------------------------------------------------------------
# Connectivity probe
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ProbeResult:
    provider_id: str
    ok: bool
    detail: str
    model: str | None = None
    endpoint: str | None = None
    attempts: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider_id,
            "ok": self.ok,
            "detail": self.detail,
            "model": self.model,
            "endpoint": self.endpoint,
            "attempts": list(self.attempts),
        }


def _http_json(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    payload: dict | None = None,
    timeout: float = 20.0,
) -> tuple[int, str]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=body, method=method)
    request.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", "replace")[:2000]
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")[:2000]
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        return 0, str(exc)


def _probe_anthropic_endpoint(
    spec: ProviderSpec, token: str, model: str
) -> tuple[int, str]:
    return _http_json(
        f"{spec.anthropic_base_url.rstrip('/')}/v1/messages",
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "x-api-key": token,
            "anthropic-version": _ANTHROPIC_VERSION,
        },
        payload={
            "model": model,
            "max_tokens": 8,
            "messages": [{"role": "user", "content": "Reply with exactly: ok"}],
        },
    )


def probe_provider(provider_id: str, *, model: str | None = None) -> ProbeResult:
    """Cheap live check that the provider accepts our token."""
    spec = get_provider_spec(provider_id)
    token = resolve_provider_token(spec.id)
    if not token:
        return ProbeResult(
            provider_id=spec.id,
            ok=False,
            detail=(
                f"no token: export {spec.token_env} or run "
                f"`tillm provider set {spec.id}`"
            ),
        )

    if spec.anthropic_base_url:
        models = (model,) if model else (spec.probe_models or (spec.default_model or "",))
        attempts: list[str] = []
        for candidate in [m for m in models if m]:
            status, body = _probe_anthropic_endpoint(spec, token, candidate)
            attempts.append(f"{candidate}:{status}")
            if status == 200:
                return ProbeResult(
                    provider_id=spec.id,
                    ok=True,
                    detail=f"messages endpoint OK (model {candidate})",
                    model=candidate,
                    endpoint=spec.anthropic_base_url,
                    attempts=tuple(attempts),
                )
            if status in (401, 403):
                return ProbeResult(
                    provider_id=spec.id,
                    ok=False,
                    detail=f"auth rejected (HTTP {status}): {body[:200]}",
                    endpoint=spec.anthropic_base_url,
                    attempts=tuple(attempts),
                )
        return ProbeResult(
            provider_id=spec.id,
            ok=False,
            detail=f"no probe model accepted; last response: {body[:200]}",
            endpoint=spec.anthropic_base_url,
            attempts=tuple(attempts),
        )

    if spec.openai_base_url:
        status, body = _http_json(
            f"{spec.openai_base_url.rstrip('/')}/models",
            headers={"Authorization": f"Bearer {token}"},
        )
        ok = status == 200
        return ProbeResult(
            provider_id=spec.id,
            ok=ok,
            detail=f"HTTP {status}" + ("" if ok else f": {body[:200]}"),
            endpoint=spec.openai_base_url,
        )

    return ProbeResult(
        provider_id=spec.id,
        ok=True,
        detail="native provider; token present (no remote probe performed)",
    )


__all__ = [
    "ProviderSpec",
    "ProbeResult",
    "UnknownProviderError",
    "client_protocol",
    "get_provider_spec",
    "iter_provider_specs",
    "normalize_provider_id",
    "probe_provider",
    "provider_default_model",
    "provider_env_overlay",
    "resolve_provider_token",
    "resolve_request_provider",
    "save_provider_token",
    "stored_provider_entry",
]
