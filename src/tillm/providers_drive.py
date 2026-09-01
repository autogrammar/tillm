"""Provider resolution for shell drives and client env overlays."""

from __future__ import annotations

import os

from tillm.providers_registry import get_provider_spec, normalize_provider_id
from tillm.providers_store import (
    get_default_provider,
    get_stored_provider_order,
    provider_default_model,
    resolve_provider_token,
)
from tillm.providers_types import (
    CLIENT_PROTOCOLS,
    PROVIDER_EXHAUSTION_MARKERS,
    SUBSCRIPTION_CLIENTS,
    SUBSCRIPTION_DRIVE_PROVIDER,
    UnknownProviderError,
    is_subscription_order_token,
)


def client_protocol(client_id: str) -> str | None:
    return CLIENT_PROTOCOLS.get((client_id or "").strip().lower())


def provider_env_overlay(client_id: str, provider_id: str) -> dict[str, str]:
    """Env vars that point ``client_id`` at ``provider_id``."""
    spec = get_provider_spec(provider_id)
    protocol = client_protocol(client_id)
    if protocol is None:
        raise ValueError(
            f"client {client_id!r} has no provider protocol mapping; "
            f"providers work with: {', '.join(sorted(CLIENT_PROTOCOLS))}"
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
        token = "local"

    overlay: dict[str, str] = {}
    if protocol == "anthropic":
        if spec.anthropic_base_url:
            overlay["ANTHROPIC_BASE_URL"] = spec.anthropic_base_url
            overlay["ANTHROPIC_AUTH_TOKEN"] = token or ""
        elif token:
            overlay["ANTHROPIC_API_KEY"] = token
        model = provider_default_model(spec.id)
        if spec.anthropic_base_url and model:
            overlay.setdefault("ANTHROPIC_MODEL", model)
    else:
        if token:
            overlay["OPENAI_API_KEY"] = token
        if spec.openai_base_url:
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


def provider_compatible_with_client(client_id: str, provider_id: str) -> bool:
    """Whether ``provider_id`` (or subscription sentinel) can drive ``client_id``."""
    if provider_id == SUBSCRIPTION_DRIVE_PROVIDER:
        return (client_id or "").strip().lower() in SUBSCRIPTION_CLIENTS
    protocol = client_protocol(client_id)
    if protocol is None:
        return False
    try:
        spec = get_provider_spec(provider_id)
    except UnknownProviderError:
        return False
    if protocol not in spec.protocols():
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
    """Ordered provider attempts for a drive (subscription → z.ai → openrouter, …)."""
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
    if (client_id or "").strip().lower() in SUBSCRIPTION_CLIENTS:
        return (SUBSCRIPTION_DRIVE_PROVIDER,)
    return ()


def is_provider_exhaustion(*, stdout: str = "", stderr: str = "", message: str = "") -> bool:
    """True when failure looks like quota/rate-limit/credits (try next provider)."""
    blob = f"{stdout}\n{stderr}\n{message}".lower()
    return any(marker in blob for marker in PROVIDER_EXHAUSTION_MARKERS)
