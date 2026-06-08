"""Build and execute controlled shell LLM invocations."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tillm.registry import ShellClientSpec, get_client_spec


class TillmError(RuntimeError):
    """Base error for SLLM control failures."""


TillmError = TillmError


class UnknownClientError(TillmError):
    """Requested client is not registered."""


class ClientUnavailableError(TillmError):
    """Registered client command is not available in PATH."""


@dataclass(frozen=True)
class ShellDriveRequest:
    client_id: str
    prompt: str
    project: Path = field(default_factory=Path.cwd)
    execute: bool = False
    dry_run: bool = False
    extra_args: tuple[str, ...] = ()
    timeout_seconds: float | None = 900.0
    prompt_dir: Path | None = None


@dataclass(frozen=True)
class ShellDrivePlan:
    spec: ShellClientSpec
    command_path: str
    argv: tuple[str, ...]
    cwd: Path
    prompt_path: Path
    stdin_text: str | None = None

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
        }


@dataclass(frozen=True)
class ShellDriveResult:
    ok: bool
    client_id: str
    command: tuple[str, ...]
    prompt_path: Path
    executed: bool
    dry_run: bool
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    message: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "client_id": self.client_id,
            "command": list(self.command),
            "prompt_path": str(self.prompt_path),
            "executed": self.executed,
            "dry_run": self.dry_run,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "message": self.message,
            "backend": "tillm_shell",
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


def build_drive_plan(request: ShellDriveRequest) -> ShellDrivePlan:
    spec = _resolve_spec(request.client_id)
    command_path = _resolve_command(spec)
    prompt_path = save_prompt(
        request.prompt,
        project=request.project,
        prompt_dir=request.prompt_dir,
    )
    argv = [command_path, *spec.argv_prefix, *request.extra_args]
    stdin_text: str | None = None

    if spec.prompt_mode == "message-file":
        argv.extend([spec.prompt_file_flag, str(prompt_path)])
    elif spec.prompt_mode == "arg":
        argv.append(request.prompt.strip())
    else:
        stdin_text = request.prompt.strip() + "\n"

    return ShellDrivePlan(
        spec=spec,
        command_path=command_path,
        argv=tuple(argv),
        cwd=request.project.resolve(),
        prompt_path=prompt_path,
        stdin_text=stdin_text,
    )


def _timeout_value(timeout_seconds: float | None) -> float | None:
    if timeout_seconds is None:
        return None
    value = float(timeout_seconds)
    return None if value <= 0 else value


def drive_shell_llm(request: ShellDriveRequest) -> ShellDriveResult:
    plan = build_drive_plan(request)
    if request.dry_run or not request.execute:
        return ShellDriveResult(
            ok=True,
            client_id=plan.spec.id,
            command=plan.argv,
            prompt_path=plan.prompt_path,
            executed=False,
            dry_run=True,
            message="dry-run: command planned but not executed",
        )

    try:
        proc = subprocess.run(
            list(plan.argv),
            cwd=plan.cwd,
            input=plan.stdin_text,
            capture_output=True,
            text=True,
            check=False,
            timeout=_timeout_value(request.timeout_seconds),
            env=dict(os.environ),
        )
    except subprocess.TimeoutExpired as exc:
        return ShellDriveResult(
            ok=False,
            client_id=plan.spec.id,
            command=plan.argv,
            prompt_path=plan.prompt_path,
            executed=True,
            dry_run=False,
            exit_code=None,
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
            message=f"timeout after {request.timeout_seconds}s",
        )
    except OSError as exc:
        return ShellDriveResult(
            ok=False,
            client_id=plan.spec.id,
            command=plan.argv,
            prompt_path=plan.prompt_path,
            executed=True,
            dry_run=False,
            exit_code=None,
            message=str(exc),
        )

    return ShellDriveResult(
        ok=proc.returncode == 0,
        client_id=plan.spec.id,
        command=plan.argv,
        prompt_path=plan.prompt_path,
        executed=True,
        dry_run=False,
        exit_code=proc.returncode,
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
        message="completed" if proc.returncode == 0 else "client command failed",
    )


def result_from_error(client_id: str, exc: Exception) -> dict[str, Any]:
    return {
        "ok": False,
        "client_id": client_id,
        "backend": "tillm_shell",
        "error": type(exc).__name__,
        "message": str(exc),
    }


__all__ = [
    "ClientUnavailableError",
    "TillmError",
    "ShellDrivePlan",
    "ShellDriveRequest",
    "ShellDriveResult",
    "TillmError",
    "UnknownClientError",
    "build_drive_plan",
    "drive_shell_llm",
    "result_from_error",
    "save_prompt",
]
