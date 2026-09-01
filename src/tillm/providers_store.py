"""Secure token storage for provider credentials."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

from tillm.providers_registry import get_provider_spec, normalize_provider_id
from tillm.providers_types import is_subscription_order_token


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
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)
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
    """Persist the fallback queue used when ``TILLM_PROVIDER_ORDER`` is unset."""
    normalized: list[str] = []
    for raw in order:
        token = (raw or "").strip()
        if not token:
            continue
        if is_subscription_order_token(token):
            candidate = "subscription"
        else:
            get_provider_spec(token)
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
