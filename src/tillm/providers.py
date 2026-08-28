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
    "qwen-code": "openai",
}


@dataclass(frozen=True)
class ProviderSpec:
    id: str
    label: str
    kind: str  # "api" | "subscription"
    token_env: str
    docs_url: str = ""
    # Where the operator creates/copies the token — shown before token prompts.
    token_url: str = ""
    # Base URLs per protocol; None means "native endpoint of that protocol".
    anthropic_base_url: str | None = None
    openai_base_url: str | None = None
    # Models to try, in order, when probing connectivity.
    probe_models: tuple[str, ...] = ()
    # Curated model choices for pickers, newest/most useful first.
    models: tuple[str, ...] = ()
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
    # Ordered by popularity / recency — this is the display order in pickers.
    ProviderSpec(
        id="anthropic",
        label="Anthropic (Claude)",
        kind="subscription",
        token_env="ANTHROPIC_API_KEY",
        docs_url="https://docs.anthropic.com",
        token_url="https://console.anthropic.com/settings/keys",
        anthropic_base_url=None,  # native
        models=("sonnet", "opus", "haiku"),
        notes="claude-code native; subscription login or ANTHROPIC_API_KEY.",
    ),
    ProviderSpec(
        id="openai",
        label="OpenAI (GPT)",
        kind="api",
        token_env="OPENAI_API_KEY",
        docs_url="https://platform.openai.com/docs",
        token_url="https://platform.openai.com/api-keys",
        openai_base_url=None,  # native
        models=("gpt-5.1", "gpt-5.1-codex", "gpt-5-mini"),
        notes="codex/aider native endpoint.",
    ),
    ProviderSpec(
        id="z.ai",
        label="Z.ai (GLM)",
        kind="api",
        token_env="ZAI_API_KEY",
        docs_url="https://docs.z.ai",
        token_url="https://z.ai/manage-apikey/apikey-list",
        anthropic_base_url="https://api.z.ai/api/anthropic",
        openai_base_url="https://api.z.ai/api/coding/paas/v4",
        probe_models=("glm-4.7", "glm-4.6", "glm-4.5"),
        default_model="glm-4.7",
        aliases=("zai", "z-ai", "glm", "zhipu"),
        models=("glm-4.7", "glm-4.6", "glm-4.5", "glm-4.5-air"),
        notes="GLM coding plan; Anthropic-compatible endpoint drives claude-code.",
    ),
    ProviderSpec(
        id="deepseek",
        label="DeepSeek",
        kind="api",
        token_env="DEEPSEEK_API_KEY",
        docs_url="https://api-docs.deepseek.com",
        token_url="https://platform.deepseek.com/api_keys",
        anthropic_base_url="https://api.deepseek.com/anthropic",
        openai_base_url="https://api.deepseek.com",
        probe_models=("deepseek-chat",),
        default_model="deepseek-chat",
        models=("deepseek-chat", "deepseek-reasoner"),
        notes="V3/R1; Anthropic-compatible endpoint drives claude-code.",
    ),
    ProviderSpec(
        id="google",
        label="Google (Gemini)",
        kind="api",
        token_env="GEMINI_API_KEY",
        docs_url="https://ai.google.dev/gemini-api/docs",
        token_url="https://aistudio.google.com/app/apikey",
        openai_base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        aliases=("gemini",),
        models=("gemini-3-pro-preview", "gemini-2.5-pro", "gemini-2.5-flash"),
        notes="gemini-cli native; OpenAI-compatible endpoint for aider/codex.",
    ),
    ProviderSpec(
        id="openrouter",
        label="OpenRouter",
        kind="api",
        token_env="OPENROUTER_API_KEY",
        docs_url="https://openrouter.ai/docs",
        token_url="https://openrouter.ai/settings/keys",
        openai_base_url="https://openrouter.ai/api/v1",
        aliases=("or",),
        notes="Multi-model gateway; OpenAI-compatible (aider/codex lane).",
    ),
    ProviderSpec(
        id="moonshot",
        label="Moonshot (Kimi)",
        kind="api",
        token_env="MOONSHOT_API_KEY",
        docs_url="https://platform.moonshot.ai/docs",
        token_url="https://platform.moonshot.ai/console/api-keys",
        anthropic_base_url="https://api.moonshot.ai/anthropic",
        openai_base_url="https://api.moonshot.ai/v1",
        probe_models=("kimi-k2.5", "kimi-k2-turbo-preview", "kimi-k2"),
        default_model="kimi-k2.5",
        aliases=("kimi",),
        models=("kimi-k2.5", "kimi-k2-turbo-preview", "kimi-k2"),
        notes="Kimi K2; Anthropic-compatible endpoint drives claude-code.",
    ),
    ProviderSpec(
        id="xai",
        label="xAI (Grok)",
        kind="api",
        token_env="XAI_API_KEY",
        docs_url="https://docs.x.ai",
        token_url="https://console.x.ai",
        openai_base_url="https://api.x.ai/v1",
        aliases=("grok",),
        models=("grok-4.1", "grok-4", "grok-code-fast-1"),
        notes="Grok; OpenAI-compatible (aider/codex lane).",
    ),
    ProviderSpec(
        id="groq",
        label="Groq",
        kind="api",
        token_env="GROQ_API_KEY",
        docs_url="https://console.groq.com/docs",
        token_url="https://console.groq.com/keys",
        openai_base_url="https://api.groq.com/openai/v1",
        models=("llama-3.3-70b-versatile",),
        notes="Fast open-model inference; OpenAI-compatible.",
    ),
    ProviderSpec(
        id="mistral",
        label="Mistral",
        kind="api",
        token_env="MISTRAL_API_KEY",
        docs_url="https://docs.mistral.ai",
        token_url="https://console.mistral.ai/api-keys",
        openai_base_url="https://api.mistral.ai/v1",
        models=("mistral-large-latest", "codestral-latest", "devstral-medium-latest"),
        notes="OpenAI-compatible (aider/codex lane).",
    ),
    ProviderSpec(
        id="minimax",
        label="MiniMax (M2)",
        kind="api",
        token_env="MINIMAX_API_KEY",
        docs_url="https://platform.minimax.io/docs",
        token_url="https://platform.minimax.io/user-center/basic-information/interface-key",
        anthropic_base_url="https://api.minimax.io/anthropic",
        openai_base_url="https://api.minimax.io/v1",
        probe_models=("MiniMax-M2",),
        default_model="MiniMax-M2",
        models=("MiniMax-M2",),
        notes="M2; Anthropic-compatible endpoint drives claude-code.",
    ),
    ProviderSpec(
        id="qwen",
        label="Qwen (DashScope)",
        kind="api",
        token_env="DASHSCOPE_API_KEY",
        docs_url="https://www.alibabacloud.com/help/en/model-studio",
        token_url="https://bailian.console.aliyun.com/?apiKey=1",
        openai_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        aliases=("dashscope",),
        models=("qwen3-coder-plus", "qwen3-max", "qwen-max"),
        notes="Qwen3 family; OpenAI-compatible; qwen-code client lane.",
    ),
    ProviderSpec(
        id="ollama",
        label="Ollama (local)",
        kind="local",
        token_env="OLLAMA_API_KEY",
        docs_url="https://docs.ollama.com",
        token_url="",
        openai_base_url="http://localhost:11434/v1",
        notes="Local models, no token needed; requires `ollama serve`.",
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


def set_default_provider(provider_id: str) -> Path:
    """Persist the provider used when neither --provider nor env is set."""
    spec = get_provider_spec(provider_id)
    store = _load_store()
    store["_default"] = {"provider": spec.id}
    return _write_store(store)


def get_default_provider() -> str | None:
    entry = _load_store().get("_default")
    if isinstance(entry, dict):
        value = str(entry.get("provider") or "").strip()
        return value or None
    return None


def set_provider_order(order: list[str]) -> Path:
    """Persist the fallback queue used when ``TILLM_PROVIDER_ORDER`` is unset.

    Tokens are provider ids/aliases or a subscription token (``subscription``).
    Raises ``UnknownProviderError`` on anything else, so a typo cannot
    silently drop a provider from the queue.
    """
    normalized: list[str] = []
    for raw in order:
        token = (raw or "").strip()
        if not token:
            continue
        if is_subscription_order_token(token):
            candidate = "subscription"
        else:
            get_provider_spec(token)  # raises UnknownProviderError
            candidate = normalize_provider_id(token)
        if candidate not in normalized:
            normalized.append(candidate)
    store = _load_store()
    entry = dict(store.get("_default") or {})
    if normalized:
        entry["order"] = normalized
    else:
        entry.pop("order", None)
    store["_default"] = entry
    return _write_store(store)


def get_stored_provider_order() -> tuple[str, ...]:
    entry = _load_store().get("_default")
    if isinstance(entry, dict):
        raw = entry.get("order")
        if isinstance(raw, list):
            return tuple(str(item).strip() for item in raw if str(item).strip())
    return ()


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
    if not token and spec.kind == "local":
        token = "local"  # openai-protocol clients require a non-empty key

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
    """Provider for this drive: explicit arg > TILLM_PROVIDER env > stored default."""
    raw = (
        (explicit or "").strip()
        or os.environ.get("TILLM_PROVIDER", "").strip()
        or (get_default_provider() or "")
    )
    return normalize_provider_id(raw) if raw else None


# Sentinel passed on ShellDriveRequest.provider to force native client auth (e.g.
# claude-code subscription login) with no tillm env overlay.
SUBSCRIPTION_DRIVE_PROVIDER = "__subscription__"

_SUBSCRIPTION_ORDER_TOKENS = frozenset(
    {"subscription", "claude-subscription", "native", "claude-native"}
)

# Clients that can use the subscription/native attempt (no provider overlay).
_SUBSCRIPTION_CLIENTS = frozenset({"claude-code"})

_PROVIDER_EXHAUSTION_MARKERS = (
    "429",
    "402",
    "limit exhausted",
    "rate limit",
    "requires more credits",
    "insufficient credits",
    "insufficient quota",
    "quota exceeded",
    "billing",
    "weekly/monthly limit",
    "usage limit",
    "credit balance",
)


def is_subscription_order_token(token: str) -> bool:
    return (token or "").strip().lower() in _SUBSCRIPTION_ORDER_TOKENS


def provider_compatible_with_client(client_id: str, provider_id: str) -> bool:
    """Whether ``provider_id`` (or subscription sentinel) can drive ``client_id``."""
    if provider_id == SUBSCRIPTION_DRIVE_PROVIDER:
        return (client_id or "").strip().lower() in _SUBSCRIPTION_CLIENTS
    protocol = client_protocol(client_id)
    if protocol is None:
        return False
    try:
        spec = get_provider_spec(provider_id)
    except UnknownProviderError:
        return False
    if protocol not in spec.protocols():
        # openrouter fallback: claude-code can hand off to aider when available.
        if (
            provider_id == "openrouter"
            and (client_id or "").strip().lower() == "claude-code"
        ):
            from tillm.compat import is_client_available

            return is_client_available("aider")
        return False
    if spec.kind == "api" and not resolve_provider_token(spec.id):
        return False
    return True


def resolve_drive_client_id(client_id: str, provider_id: str | None) -> str:
    """Client to spawn for a provider attempt (openrouter may switch claude-code → aider)."""
    if (
        provider_id == "openrouter"
        and (client_id or "").strip().lower() == "claude-code"
    ):
        from tillm.compat import is_client_available

        if is_client_available("aider"):
            return "aider"
    return client_id


def resolve_drive_model(
    client_id: str,
    provider_id: str | None,
    requested: str | None,
) -> str | None:
    """Pick a model for a provider attempt (avoid openrouter/ prefixes on z.ai)."""
    model = (requested or "").strip()
    if provider_id in {None, SUBSCRIPTION_DRIVE_PROVIDER}:
        return model or None
    if not model:
        return provider_default_model(provider_id)
    if provider_id == "openrouter":
        return model if model.startswith("openrouter/") else f"openrouter/{model}"
    if model.startswith("openrouter/"):
        return provider_default_model(provider_id)
    return model


def resolve_provider_drive_attempts(
    client_id: str,
    *,
    explicit_provider: str | None = None,
) -> tuple[str | None, ...]:
    """Ordered provider attempts for a drive (subscription → z.ai → openrouter, …).

  Precedence:
  - explicit ``--provider`` on CLI → single attempt, no automatic fallback
  - ``TILLM_PROVIDER_ORDER`` (comma-separated) when set
  - stored order (``tillm provider order …``) when configured
  - else single ``TILLM_PROVIDER`` / stored default (legacy behaviour)
    """
    if (explicit_provider or "").strip():
        token = explicit_provider.strip()
        if is_subscription_order_token(token):
            return (SUBSCRIPTION_DRIVE_PROVIDER,)
        return (normalize_provider_id(token),)

    order_raw = os.environ.get("TILLM_PROVIDER_ORDER", "").strip()
    order_tokens = (
        [raw for raw in order_raw.split(",")]
        if order_raw
        else list(get_stored_provider_order())
    )
    if order_tokens:
        attempts: list[str | None] = []
        for raw in order_tokens:
            token = raw.strip()
            if not token:
                continue
            if is_subscription_order_token(token):
                candidate = SUBSCRIPTION_DRIVE_PROVIDER
            else:
                try:
                    get_provider_spec(token)
                except UnknownProviderError:
                    continue
                candidate = normalize_provider_id(token)
            if not provider_compatible_with_client(client_id, candidate):
                continue
            if candidate not in attempts:
                attempts.append(candidate)
        if attempts:
            return tuple(attempts)

    single = resolve_request_provider(None)
    if single and provider_compatible_with_client(client_id, single):
        return (single,)
    if (client_id or "").strip().lower() in _SUBSCRIPTION_CLIENTS:
        return (SUBSCRIPTION_DRIVE_PROVIDER,)
    return ()


def is_provider_exhaustion(*, stdout: str = "", stderr: str = "", message: str = "") -> bool:
    """True when failure looks like quota/rate-limit/credits (try next provider)."""
    blob = f"{stdout}\n{stderr}\n{message}".lower()
    return any(marker in blob for marker in _PROVIDER_EXHAUSTION_MARKERS)


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
    if not token and spec.kind == "local":
        token = "local"
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
        if model:
            models: tuple[str, ...] = (model,)
        else:
            stored = stored_provider_entry(spec.id).get("model", "").strip()
            ordered = [stored] if stored else []
            ordered += [m for m in spec.probe_models if m not in ordered]
            if spec.default_model and spec.default_model not in ordered:
                ordered.append(spec.default_model)
            models = tuple(ordered) or ("",)
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
        headers = {"Authorization": f"Bearer {token}"}
        if spec.id == "openrouter":
            headers.update(
                {
                    "HTTP-Referer": os.getenv(
                        "OPENROUTER_APP_URL", "https://github.com/autogrammar/tillm"
                    ),
                    "X-OpenRouter-Title": os.getenv("OPENROUTER_APP_NAME", "tillm"),
                }
            )
        status, body = _http_json(
            f"{spec.openai_base_url.rstrip('/')}/models",
            headers=headers,
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


@dataclass(frozen=True)
class ModelListing:
    provider_id: str
    models: tuple[str, ...]
    source: str  # "live" | "curated"
    detail: str = ""


def _parse_models_payload(body: str) -> tuple[str, ...]:
    try:
        data = json.loads(body)
    except ValueError:
        return ()
    rows = data.get("data") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        return ()
    entries = []
    for row in rows:
        if isinstance(row, dict) and row.get("id"):
            entries.append((row.get("created") or 0, str(row["id"])))
    # Newest first when the API exposes creation timestamps.
    entries.sort(key=lambda pair: pair[0], reverse=True)
    return tuple(model_id for _, model_id in entries)


def list_provider_models(provider_id: str, *, timeout: float = 10.0) -> ModelListing:
    """Live model list from the provider API; curated fallback when unavailable.

    Hardcoded model lists go stale (users already run models newer than any
    snapshot); this asks the provider itself and only falls back to the
    curated ``spec.models``.
    """
    spec = get_provider_spec(provider_id)
    token = resolve_provider_token(spec.id)
    if not token and spec.kind == "local":
        token = "local"

    attempts: list[str] = []
    if token:
        endpoints = []
        if spec.openai_base_url:
            endpoints.append(
                (
                    f"{spec.openai_base_url.rstrip('/')}/models",
                    {"Authorization": f"Bearer {token}"},
                )
            )
        if spec.anthropic_base_url:
            endpoints.append(
                (
                    f"{spec.anthropic_base_url.rstrip('/')}/v1/models",
                    {
                        "Authorization": f"Bearer {token}",
                        "x-api-key": token,
                        "anthropic-version": _ANTHROPIC_VERSION,
                    },
                )
            )
        if spec.id == "anthropic":
            endpoints.append(
                (
                    "https://api.anthropic.com/v1/models",
                    {"x-api-key": token, "anthropic-version": _ANTHROPIC_VERSION},
                )
            )
        for url, headers in endpoints:
            status, body = _http_json(url, headers=headers, timeout=timeout)
            attempts.append(f"{url}:{status}")
            if status == 200:
                models = _parse_models_payload(body)
                if models:
                    return ModelListing(
                        provider_id=spec.id,
                        models=models,
                        source="live",
                        detail=url,
                    )
    return ModelListing(
        provider_id=spec.id,
        models=spec.models,
        source="curated",
        detail="; ".join(attempts) if attempts else "no token / no endpoint",
    )


@dataclass(frozen=True)
class DiagnosisItem:
    level: str  # "ok" | "warn" | "fail"
    code: str
    message: str
    fix: str = ""


@dataclass(frozen=True)
class ProviderDiagnosis:
    provider_id: str
    ok: bool
    items: tuple[DiagnosisItem, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider_id,
            "ok": self.ok,
            "items": [vars(item) for item in self.items],
        }


def diagnose_provider(provider_id: str) -> ProviderDiagnosis:
    """Auto-diagnostics: token, endpoint, the *configured* model, client binaries."""
    import shutil as _shutil

    spec = get_provider_spec(provider_id)
    items: list[DiagnosisItem] = []

    token = resolve_provider_token(spec.id)
    if token or spec.kind in ("local", "subscription"):
        items.append(DiagnosisItem("ok", "token", "present" if token else "not required"))
    else:
        items.append(
            DiagnosisItem(
                "fail",
                "token",
                f"no token ({spec.token_env})",
                fix=f"tillm provider set {spec.id}",
            )
        )

    configured_model = stored_provider_entry(spec.id).get("model", "").strip() or None
    effective_model = configured_model or spec.default_model

    if token or spec.kind == "local":
        listing = list_provider_models(spec.id)
        if listing.source == "live":
            items.append(
                DiagnosisItem("ok", "endpoint", f"model list fetched live ({len(listing.models)} models)")
            )
            if effective_model and listing.models and effective_model not in listing.models:
                near = [m for m in listing.models if effective_model.split("-")[0] in m][:3]
                items.append(
                    DiagnosisItem(
                        "warn",
                        "model_unknown",
                        f"configured model {effective_model!r} not in the provider's live list",
                        fix=f"try: {', '.join(near) or listing.models[0]}",
                    )
                )
        else:
            items.append(
                DiagnosisItem("warn", "endpoint", f"live model list unavailable ({listing.detail})")
            )

        if spec.kind != "subscription":
            result = probe_provider(spec.id, model=effective_model if spec.anthropic_base_url else None)
            if result.ok:
                items.append(
                    DiagnosisItem("ok", "probe", f"probe OK ({result.model or 'endpoint'})")
                )
            else:
                fallback = probe_provider(spec.id) if effective_model else result
                if effective_model and fallback.ok:
                    items.append(
                        DiagnosisItem(
                            "fail",
                            "model_rejected",
                            f"configured model {effective_model!r} rejected, "
                            f"but {fallback.model!r} works",
                            fix=f"tillm provider set {spec.id} --model {fallback.model}",
                        )
                    )
                else:
                    items.append(
                        DiagnosisItem("fail", "probe", result.detail, fix=f"tillm provider test {spec.id}")
                    )

    from tillm.registry import available_client_ids

    available = set(available_client_ids())
    compatible = spec.compatible_clients()
    present = [c for c in compatible if c in available]
    if present:
        items.append(DiagnosisItem("ok", "clients", f"clients on PATH: {', '.join(present)}"))
    elif compatible:
        items.append(
            DiagnosisItem(
                "warn",
                "clients",
                f"no compatible client on PATH ({', '.join(compatible)})",
                fix=f"install one of: {', '.join(compatible)}",
            )
        )

    ok = not any(item.level == "fail" for item in items)
    return ProviderDiagnosis(provider_id=spec.id, ok=ok, items=tuple(items))


__all__ = [
    "ProviderSpec",
    "ProbeResult",
    "UnknownProviderError",
    "SUBSCRIPTION_DRIVE_PROVIDER",
    "client_protocol",
    "get_provider_spec",
    "DiagnosisItem",
    "ModelListing",
    "ProviderDiagnosis",
    "diagnose_provider",
    "is_provider_exhaustion",
    "is_subscription_order_token",
    "iter_provider_specs",
    "list_provider_models",
    "normalize_provider_id",
    "probe_provider",
    "get_default_provider",
    "provider_compatible_with_client",
    "provider_default_model",
    "resolve_drive_model",
    "resolve_drive_client_id",
    "resolve_provider_drive_attempts",
    "set_default_provider",
    "provider_env_overlay",
    "resolve_provider_token",
    "resolve_request_provider",
    "save_provider_token",
    "stored_provider_entry",
]
