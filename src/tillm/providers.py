"""Registry of LLM API providers usable behind shell clients.

Facade over focused submodules: registry, token store, drive resolution,
and connectivity probes.
"""

from tillm.providers_drive import (
    client_protocol,
    is_provider_exhaustion,
    provider_compatible_with_client,
    provider_env_overlay,
    resolve_drive_client_id,
    resolve_drive_model,
    resolve_provider_drive_attempts,
    resolve_request_provider,
)
from tillm.providers_probe import (
    DiagnosisItem,
    ModelListing,
    ProbeResult,
    ProviderDiagnosis,
    _http_json_impl,
    diagnose_provider,
    list_provider_models,
    probe_provider,
)
from tillm.providers_registry import (
    get_provider_spec,
    iter_provider_specs,
    normalize_provider_id,
)
from tillm.providers_store import (
    _config_path,
    _load_store,
    _write_store,
    get_default_provider,
    get_stored_provider_order,
    provider_default_model,
    resolve_provider_token,
    save_provider_token,
    set_default_provider,
    set_provider_order,
    stored_provider_entry,
)
from tillm.providers_types import (
    ProviderSpec,
    SUBSCRIPTION_DRIVE_PROVIDER,
    UnknownProviderError,
    is_subscription_order_token,
)


def _http_json(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    payload: dict | None = None,
    timeout: float = 20.0,
) -> tuple[int, str]:
    return _http_json_impl(
        url, method=method, headers=headers, payload=payload, timeout=timeout
    )


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
    "get_stored_provider_order",
    "provider_compatible_with_client",
    "provider_default_model",
    "resolve_drive_model",
    "resolve_drive_client_id",
    "resolve_provider_drive_attempts",
    "set_default_provider",
    "set_provider_order",
    "provider_env_overlay",
    "resolve_provider_token",
    "resolve_request_provider",
    "save_provider_token",
    "stored_provider_entry",
]
