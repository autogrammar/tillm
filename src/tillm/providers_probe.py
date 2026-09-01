"""Connectivity probes and model listing for LLM providers."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from tillm.providers_registry import get_provider_spec
from tillm.providers_store import resolve_provider_token, stored_provider_entry
from tillm.providers_types import (
    _ANTHROPIC_VERSION,
    DiagnosisItem,
    ModelListing,
    ProbeResult,
    ProviderDiagnosis,
    ProviderSpec,
)

__all__ = [
    "ModelListing",
    "ProbeResult",
    "ProviderDiagnosis",
    "DiagnosisItem",
    "diagnose_provider",
    "list_provider_models",
    "probe_provider",
]


def _http_json_impl(
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


def _http_json(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    payload: dict | None = None,
    timeout: float = 20.0,
) -> tuple[int, str]:
    """Delegate through the facade so tests can monkeypatch ``tillm.providers``."""
    from tillm.providers import _http_json as facade_http

    return facade_http(url, method=method, headers=headers, payload=payload, timeout=timeout)


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
    entries.sort(key=lambda pair: pair[0], reverse=True)
    return tuple(model_id for _, model_id in entries)


def list_provider_models(provider_id: str, *, timeout: float = 10.0) -> ModelListing:
    """Live model list from the provider API; curated fallback when unavailable."""
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


def diagnose_provider(provider_id: str) -> ProviderDiagnosis:
    """Auto-diagnostics: token, endpoint, the *configured* model, client binaries."""
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
                DiagnosisItem(
                    "ok",
                    "endpoint",
                    f"model list fetched live ({len(listing.models)} models)",
                )
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
                        DiagnosisItem(
                            "fail", "probe", result.detail, fix=f"tillm provider test {spec.id}"
                        )
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
