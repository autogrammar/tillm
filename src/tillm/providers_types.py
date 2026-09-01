"""Shared types and constants for LLM provider configuration."""

from __future__ import annotations

from dataclasses import dataclass, field

_ANTHROPIC_VERSION = "2023-06-01"

# Which wire protocol each registered client speaks (for provider overlays).
CLIENT_PROTOCOLS: dict[str, str] = {
    "claude-code": "anthropic",
    "aider": "openai",
    "codex": "openai",
    "qwen-code": "openai",
}

# Sentinel passed on ShellDriveRequest.provider to force native client auth.
SUBSCRIPTION_DRIVE_PROVIDER = "__subscription__"

SUBSCRIPTION_ORDER_TOKENS = frozenset(
    {"subscription", "claude-subscription", "native", "claude-native"}
)

# Clients that can use the subscription/native attempt (no provider overlay).
SUBSCRIPTION_CLIENTS = frozenset({"claude-code"})

PROVIDER_EXHAUSTION_MARKERS = (
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


@dataclass(frozen=True)
class ProviderSpec:
    id: str
    label: str
    kind: str  # "api" | "subscription"
    token_env: str
    docs_url: str = ""
    token_url: str = ""
    anthropic_base_url: str | None = None
    openai_base_url: str | None = None
    probe_models: tuple[str, ...] = ()
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
            client for client, proto in CLIENT_PROTOCOLS.items() if proto in protos
        )


class UnknownProviderError(ValueError):
    pass


def is_subscription_order_token(token: str) -> bool:
    return (token or "").strip().lower() in SUBSCRIPTION_ORDER_TOKENS


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


@dataclass(frozen=True)
class ModelListing:
    provider_id: str
    models: tuple[str, ...]
    source: str  # "live" | "curated"
    detail: str = ""


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
