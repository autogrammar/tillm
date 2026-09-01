"""Dataclasses and transport resolution for shell LLM drives."""

from __future__ import annotations

import os
import shlex
from dataclasses import dataclass, field
from pathlib import Path

from tillm.registry import DEFAULT_EXECUTE_PROFILE, ClientTransport, ShellClientSpec


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
