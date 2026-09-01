"""Build shell-drive execution plans from requests."""

from __future__ import annotations

import shutil
import time
from pathlib import Path

from tillm.controller_errors import (
    ClientNotReadyError,
    ClientUnavailableError,
    TillmError,
    UnknownClientError,
    UnknownProfileError,
)
from tillm.controller_types import ShellDrivePlan, ShellDriveRequest
from tillm.project_env import bootstrap_project_env
from tillm.registry import ShellClientSpec, get_client_spec, normalize_execute_profile
from tillm.validation import validate_client_readiness

_CLAUDE_MODEL_ALIASES = {"sonnet", "opus", "haiku", "fable", "default"}


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


def _resolve_command_impl(spec: ShellClientSpec) -> str:
    command_path = spec.command_path(shutil.which)
    if command_path is None:
        commands = ", ".join(spec.commands)
        raise ClientUnavailableError(f"{spec.id}: none of these commands are in PATH: {commands}")
    return command_path


def _resolve_command(spec: ShellClientSpec) -> str:
    """Delegate to the facade module so tests can monkeypatch ``tillm.controller``."""
    from tillm.controller import _resolve_command as facade_resolve

    return facade_resolve(spec)


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


def _normalize_model_for_client(client_id: str, model: str) -> str:
    """Map short model names onto vendor CLI conventions."""
    if not model or client_id != "claude-code":
        return model
    lowered = model.lower()
    if lowered in _CLAUDE_MODEL_ALIASES or lowered.startswith("claude-"):
        return model
    return f"claude-{lowered}"


def _model_for_plan(request: ShellDriveRequest, client_id: str) -> str:
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
        _resolve_execute_args(spec, execute=request.execute, profile=execute_profile),
    )
    model_args: list[str] = []
    model = _model_for_plan(request, spec.id)
    if model:
        if not spec.model_flag:
            raise ClientNotReadyError(
                f"{spec.id}: client does not support forcing a model",
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
