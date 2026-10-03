"""Build and execute controlled shell LLM invocations."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from tillm.controller_drive import (
    _drive_shell_llm_once,
    _timeout_value,
    drive_shell_llm_many,
    result_from_error,
)
from tillm.controller_errors import (
    ClientNotReadyError,
    ClientUnavailableError,
    TillmError,
    UnknownClientError,
    UnknownProfileError,
)
from tillm.controller_plan import _resolve_command_impl, build_drive_plan, save_prompt
from tillm.controller_types import (
    MultiShellDriveRequest,
    MultiShellDriveResult,
    ShellDrivePlan,
    ShellDriveRequest,
    ShellDriveResult,
    resolve_backend,
)


def _resolve_command(spec):
    return _resolve_command_impl(spec)


def drive_shell_llm(request: ShellDriveRequest) -> ShellDriveResult:
    from tillm.providers import (
        SUBSCRIPTION_DRIVE_PROVIDER,
        is_provider_exhaustion,
        resolve_drive_client_id,
        resolve_drive_model,
        resolve_provider_drive_attempts,
    )

    attempts = resolve_provider_drive_attempts(
        request.client_id,
        explicit_provider=request.provider,
    )
    if not attempts:
        return _drive_shell_llm_once(request)

    attempt_labels = tuple(
        "subscription"
        if token == SUBSCRIPTION_DRIVE_PROVIDER
        else str(token)
        for token in attempts
    )
    last: ShellDriveResult | None = None
    for provider_token in attempts:
        drive_client = resolve_drive_client_id(request.client_id, provider_token)
        attempt_request = replace(
            request,
            client_id=drive_client,
            provider=provider_token,
            model=resolve_drive_model(
                drive_client,
                provider_token,
                request.model,
            ),
        )
        if (
            len(attempts) > 1
            and not request.dry_run
            and provider_token != SUBSCRIPTION_DRIVE_PROVIDER
        ):
            # A client like opencode retries provider 429s internally for the
            # whole quota window, which would defeat this failover loop — so
            # cheap-probe the completion endpoint and skip a dead provider
            # before the client ever starts.
            from tillm.providers import probe_provider_completion

            probe = probe_provider_completion(provider_token)
            if not probe.ok and is_provider_exhaustion(
                stdout="", stderr="", message=probe.detail
            ):
                last = ShellDriveResult(
                    ok=False,
                    client_id=drive_client,
                    command=(),
                    prompt_path=Path(""),
                    executed=False,
                    dry_run=False,
                    provider=provider_token,
                    provider_attempts=attempt_labels,
                    message=f"{provider_token} preflight exhausted: {probe.detail}",
                )
                continue
        result = _drive_shell_llm_once(attempt_request)
        label = (
            "subscription"
            if provider_token == SUBSCRIPTION_DRIVE_PROVIDER
            else provider_token
        )
        result = replace(
            result,
            provider=label if result.ok else result.provider,
            provider_attempts=attempt_labels,
        )
        if result.ok:
            return replace(result, provider=label)
        if not is_provider_exhaustion(
            stdout=result.stdout,
            stderr=result.stderr,
            message=result.message,
        ):
            return result
        last = result
    assert last is not None
    return last


__all__ = [
    "ClientNotReadyError",
    "ClientUnavailableError",
    "MultiShellDriveRequest",
    "MultiShellDriveResult",
    "UnknownProfileError",
    "TillmError",
    "ShellDrivePlan",
    "ShellDriveRequest",
    "ShellDriveResult",
    "UnknownClientError",
    "build_drive_plan",
    "drive_shell_llm",
    "drive_shell_llm_many",
    "resolve_backend",
    "result_from_error",
    "save_prompt",
]
