"""Build and execute controlled shell LLM invocations."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import time
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from tillm.project_env import bootstrap_project_env
from tillm.registry import (
    DEFAULT_EXECUTE_PROFILE,
    ClientTransport,
    ShellClientSpec,
    get_client_spec,
    normalize_execute_profile,
)
from tillm.transports.binary import run_binary_drive
from tillm.transports.docker import run_docker_drive
from tillm.validation import validate_client_readiness


class TillmError(RuntimeError):
    """Base error for TILLM control failures."""


TillmError = TillmError


class UnknownClientError(TillmError):
    """Requested client is not registered."""


class ClientUnavailableError(TillmError):
    """Registered client command is not available in PATH."""


class ClientNotReadyError(TillmError):
    """Registered client is missing binary, env vars, or requested capability."""


class UnknownProfileError(TillmError):
    """Requested execute profile is not registered for the client."""


@dataclass(frozen=True)
class ShellDriveRequest:
    client_id: str
    prompt: str
    project: Path = field(default_factory=Path.cwd)
    execute: bool = False
    dry_run: bool = False
    extra_args: tuple[str, ...] = ()
    execute_profile: str = DEFAULT_EXECUTE_PROFILE
    backend: ClientTransport = "binary"
    timeout_seconds: float | None = 900.0
    prompt_dir: Path | None = None
    model: str | None = None
    provider: str | None = None


def resolve_backend(raw: str | None = None, *, spec: ShellClientSpec | None = None) -> ClientTransport:
    import os

    value = (raw or os.getenv("TILLM_BACKEND") or (spec.transport if spec else "binary")).strip().lower()
    if value in {"binary", "docker", "http"}:
        return value  # type: ignore[return-value]
    return "binary"


@dataclass(frozen=True)
class ShellDrivePlan:
    spec: ShellClientSpec
    command_path: str
    argv: tuple[str, ...]
    cwd: Path
    prompt_path: Path
    stdin_text: str | None = None
    execute_profile: str = DEFAULT_EXECUTE_PROFILE
    env_overlay: dict[str, str] = field(default_factory=dict)

    def shell_preview(self) -> str:
        return " ".join(shlex.quote(part) for part in self.argv)

    def to_dict(self) -> dict[str, object]:
        return {
            "client_id": self.spec.id,
            "command": list(self.argv),
            "shell": self.shell_preview(),
            "cwd": str(self.cwd),
            "prompt_path": str(self.prompt_path),
            "stdin": self.stdin_text is not None,
            "execute_profile": self.execute_profile,
        }


@dataclass(frozen=True)
class MultiShellDriveRequest:
    client_ids: tuple[str, ...]
    prompt: str
    project: Path = field(default_factory=Path.cwd)
    execute: bool = False
    dry_run: bool = False
    extra_args: tuple[str, ...] = ()
    execute_profile: str = DEFAULT_EXECUTE_PROFILE
    timeout_seconds: float | None = 900.0
    prompt_dir: Path | None = None
    parallel: int = 1
    fail_fast: bool = False
    quorum: int | None = None
    backend: ClientTransport = "binary"
    model: str | None = None
    provider: str | None = None


@dataclass(frozen=True)
class ShellDriveResult:
    ok: bool
    client_id: str
    command: tuple[str, ...]
    prompt_path: Path
    executed: bool
    dry_run: bool
    execute_profile: str = DEFAULT_EXECUTE_PROFILE
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    message: str = ""
    provider: str | None = None
    provider_attempts: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "ok": self.ok,
            "client_id": self.client_id,
            "command": list(self.command),
            "prompt_path": str(self.prompt_path),
            "executed": self.executed,
            "dry_run": self.dry_run,
            "execute_profile": self.execute_profile,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "message": self.message,
            "backend": "tillm_shell",
        }
        if self.provider is not None:
            payload["provider"] = self.provider
        if self.provider_attempts:
            payload["provider_attempts"] = list(self.provider_attempts)
        return payload


@dataclass(frozen=True)
class MultiShellDriveResult:
    ok: bool
    client_ids: tuple[str, ...]
    results: tuple[ShellDriveResult, ...]
    succeeded: int
    failed: int
    executed: bool
    dry_run: bool
    message: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "client_ids": list(self.client_ids),
            "succeeded": self.succeeded,
            "failed": self.failed,
            "executed": self.executed,
            "dry_run": self.dry_run,
            "message": self.message,
            "results": [result.to_dict() for result in self.results],
            "backend": "tillm_shell_matrix",
        }


def _prompt_root(project: Path, prompt_dir: Path | None = None) -> Path:
    if prompt_dir is not None:
        return prompt_dir.expanduser().resolve()
    return project.resolve() / ".koru" / "tillm" / "prompts"


def save_prompt(prompt: str, *, project: Path, prompt_dir: Path | None = None) -> Path:
    text = prompt.strip()
    if not text:
        raise TillmError("refusing to drive an empty prompt")
    root = _prompt_root(project, prompt_dir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"prompt-{time.strftime('%Y%m%d-%H%M%S')}-{time.monotonic_ns():x}.md"
    path.write_text(text + "\n", encoding="utf-8")
    return path


def _resolve_spec(client_id: str) -> ShellClientSpec:
    spec = get_client_spec(client_id)
    if spec is None:
        raise UnknownClientError(f"unknown shell LLM client: {client_id!r}")
    return spec


def _resolve_command(spec: ShellClientSpec) -> str:
    command_path = spec.command_path(shutil.which)
    if command_path is None:
        commands = ", ".join(spec.commands)
        raise ClientUnavailableError(f"{spec.id}: none of these commands are in PATH: {commands}")
    return command_path


def _validate_request(request: ShellDriveRequest, spec: ShellClientSpec) -> None:
    if request.dry_run and not spec.supports_dry_run:
        raise ClientNotReadyError(f"{spec.id}: client does not support dry-run")
    if request.execute:
        readiness = validate_client_readiness(spec.id, require_execute=True)
        if not readiness.ok:
            raise ClientNotReadyError("; ".join(readiness.errors))


def _resolve_execute_args(spec: ShellClientSpec, *, execute: bool, profile: str) -> tuple[str, ...]:
    if not execute:
        return ()
    try:
        return spec.profile_execute_args(profile)
    except ValueError as exc:
        raise UnknownProfileError(str(exc)) from exc


_CLAUDE_MODEL_ALIASES = {"sonnet", "opus", "haiku", "fable", "default"}


def _normalize_model_for_client(client_id: str, model: str) -> str:
    """Map short model names onto vendor CLI conventions.

    Claude Code accepts bare tier aliases (``sonnet``) or full ``claude-*``
    ids; shorthand like ``sonnet-5`` needs the ``claude-`` prefix.
    """
    if not model or client_id != "claude-code":
        return model
    lowered = model.lower()
    if lowered in _CLAUDE_MODEL_ALIASES or lowered.startswith("claude-"):
        return model
    return f"claude-{lowered}"


def _model_for_plan(request: ShellDriveRequest, client_id: str) -> str:
    """Resolve the model argument for a drive, honouring the active provider.

    The ``claude-`` prefix is an Anthropic naming convention, so it may only be
    applied when Anthropic actually serves the request. A third-party provider
    overlay (z.ai, DeepSeek, …) drives claude-code through an
    Anthropic-*compatible* endpoint but keeps its own model ids, and prefixing
    those yields an unknown-model API error (e.g. ``claude-glm-5.2``).
    """
    from tillm.providers import SUBSCRIPTION_DRIVE_PROVIDER

    model = (request.model or "").strip()
    provider = (request.provider or "").strip()
    if provider and provider != SUBSCRIPTION_DRIVE_PROVIDER:
        return model
    return _normalize_model_for_client(client_id, model)


def build_drive_plan(request: ShellDriveRequest) -> ShellDrivePlan:
    bootstrap_project_env(request.project)
    spec = _resolve_spec(request.client_id)
    _validate_request(request, spec)
    command_path = _resolve_command(spec)
    prompt_path = save_prompt(
        request.prompt,
        project=request.project,
        prompt_dir=request.prompt_dir,
    )
    execute_profile = normalize_execute_profile(request.execute_profile)
    execute_args = list(
        _resolve_execute_args(spec, execute=request.execute, profile=execute_profile)
    )
    model_args: list[str] = []
    model = _model_for_plan(request, spec.id)
    if model:
        if not spec.model_flag:
            raise ClientNotReadyError(
                f"{spec.id}: client does not support forcing a model"
            )
        model_args = [spec.model_flag, model]
    argv = [command_path, *spec.argv_prefix, *execute_args, *model_args, *request.extra_args]
    stdin_text: str | None = None

    if spec.prompt_mode == "message-file":
        argv.extend([spec.prompt_file_flag, str(prompt_path)])
    elif spec.prompt_mode == "arg":
        argv.append(request.prompt.strip())
    else:
        stdin_text = request.prompt.strip() + "\n"

    from tillm.providers import (
        SUBSCRIPTION_DRIVE_PROVIDER,
        client_protocol,
        get_provider_spec,
        provider_env_overlay,
        resolve_request_provider,
    )

    env_overlay: dict[str, str] = {}
    explicit_provider = bool((request.provider or "").strip())
    if request.provider == SUBSCRIPTION_DRIVE_PROVIDER:
        env_overlay = {}
    elif request.provider:
        provider = resolve_request_provider(request.provider)
        if provider:
            env_overlay = provider_env_overlay(spec.id, provider)
    else:
        provider = resolve_request_provider(None)
        if provider:
            # An implicit provider (TILLM_PROVIDER env or stored default) must not
            # break clients it cannot serve — skip the overlay for unmapped or
            # protocol-incompatible clients. An explicit --provider still raises.
            protocol = client_protocol(spec.id)
            compatible = (
                protocol is not None and protocol in get_provider_spec(provider).protocols()
            )
            if explicit_provider or compatible:
                env_overlay = provider_env_overlay(spec.id, provider)

    return ShellDrivePlan(
        spec=spec,
        command_path=command_path,
        argv=tuple(argv),
        cwd=request.project.resolve(),
        prompt_path=prompt_path,
        stdin_text=stdin_text,
        execute_profile=execute_profile,
        env_overlay=env_overlay,
    )


def _timeout_value(timeout_seconds: float | None) -> float | None:
    if timeout_seconds is None:
        return None
    value = float(timeout_seconds)
    return None if value <= 0 else value


def _drive_result_from_exception(client_id: str, exc: Exception) -> ShellDriveResult:
    return ShellDriveResult(
        ok=False,
        client_id=client_id,
        command=(),
        prompt_path=Path.cwd(),
        executed=False,
        dry_run=True,
        message=str(exc),
    )


def _drive_one_client(request: MultiShellDriveRequest, client_id: str) -> ShellDriveResult:
    single = ShellDriveRequest(
        client_id=client_id,
        prompt=request.prompt,
        project=request.project,
        execute=request.execute,
        dry_run=request.dry_run,
        extra_args=request.extra_args,
        execute_profile=request.execute_profile,
        backend=resolve_backend(request.backend),
        timeout_seconds=request.timeout_seconds,
        prompt_dir=request.prompt_dir,
        model=request.model,
        provider=getattr(request, "provider", None),
    )
    try:
        return drive_shell_llm(single)
    except TillmError as exc:
        return _drive_result_from_exception(client_id, exc)


def drive_shell_llm_many(request: MultiShellDriveRequest) -> MultiShellDriveResult:
    if not request.client_ids:
        return MultiShellDriveResult(
            ok=False,
            client_ids=(),
            results=(),
            succeeded=0,
            failed=0,
            executed=request.execute and not request.dry_run,
            dry_run=request.dry_run or not request.execute,
            message="no clients selected",
        )

    workers = max(1, min(int(request.parallel), len(request.client_ids)))
    results: list[ShellDriveResult] = []
    pending: dict[Future[ShellDriveResult], str] = {}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for client_id in request.client_ids:
            pending[pool.submit(_drive_one_client, request, client_id)] = client_id

        while pending:
            done, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                client_id = pending.pop(future)
                try:
                    result = future.result()
                except Exception as exc:
                    result = _drive_result_from_exception(client_id, exc)
                results.append(result)

                successes = sum(1 for item in results if item.ok)
                if request.fail_fast and not result.ok:
                    for pending_future in pending:
                        pending_future.cancel()
                    pending.clear()
                    break
                if request.quorum is not None and successes >= request.quorum:
                    for pending_future in pending:
                        pending_future.cancel()
                    pending.clear()
                    break

    results.sort(key=lambda item: request.client_ids.index(item.client_id))
    succeeded = sum(1 for item in results if item.ok)
    failed = len(results) - succeeded
    executed = request.execute and not request.dry_run
    dry_run = request.dry_run or not request.execute
    quorum_met = request.quorum is None or succeeded >= request.quorum
    ok = failed == 0 if request.quorum is None else quorum_met

    if not results:
        message = "no results"
    elif request.quorum is not None and quorum_met:
        message = f"quorum met ({succeeded}/{request.quorum})"
    elif failed:
        message = f"{failed} of {len(results)} clients failed"
    else:
        message = f"all {len(results)} clients completed"

    return MultiShellDriveResult(
        ok=ok,
        client_ids=request.client_ids,
        results=tuple(results),
        succeeded=succeeded,
        failed=failed,
        executed=executed,
        dry_run=dry_run,
        message=message,
    )


def _drive_shell_llm_once(request: ShellDriveRequest) -> ShellDriveResult:
    plan = build_drive_plan(request)
    backend = resolve_backend(request.backend, spec=plan.spec)
    if backend == "docker":
        return run_docker_drive(request, plan)
    if backend == "http":
        return ShellDriveResult(
            ok=False,
            client_id=plan.spec.id,
            command=plan.argv,
            prompt_path=plan.prompt_path,
            executed=False,
            dry_run=request.dry_run or not request.execute,
            execute_profile=plan.execute_profile,
            message="http backend not implemented yet; use binary or docker",
        )
    return run_binary_drive(request, plan)


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


def result_from_error(client_id: str, exc: Exception) -> dict[str, Any]:
    return {
        "ok": False,
        "client_id": client_id,
        "backend": "tillm_shell",
        "error": type(exc).__name__,
        "message": str(exc),
    }


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
    "TillmError",
    "UnknownClientError",
    "build_drive_plan",
    "drive_shell_llm",
    "drive_shell_llm_many",
    "resolve_backend",
    "result_from_error",
    "save_prompt",
]
