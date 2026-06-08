"""Docker compose exec transport."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from typing import TYPE_CHECKING

from tillm.registry import iter_client_specs

if TYPE_CHECKING:
    from tillm.controller import ShellDrivePlan, ShellDriveRequest, ShellDriveResult


def _compose_file() -> Path:
    raw = os.getenv("TILLM_COMPOSE_FILE", "")
    if raw:
        return Path(raw).expanduser().resolve()
    return Path(__file__).resolve().parents[3] / "deploy" / "docker-compose.yml"


def docker_service_name(client_id: str) -> str:
    for spec in iter_client_specs():
        if spec.id == client_id:
            return spec.docker_service or f"tillm-{client_id}"
    return f"tillm-{client_id}"


def docker_service_status() -> list[dict[str, object]]:
    compose = _compose_file()
    if not compose.is_file():
        return [{"error": f"compose file not found: {compose}"}]
    try:
        proc = subprocess.run(
            ["docker", "compose", "-f", str(compose), "ps", "--format", "json"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return [{"error": str(exc)}]

    rows: list[dict[str, object]] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if proc.returncode != 0 and not rows:
        return [{"error": proc.stderr.strip() or "docker compose ps failed"}]
    return rows


def _docker_argv(plan: ShellDrivePlan) -> tuple[str, ...]:
    compose = _compose_file()
    service = docker_service_name(plan.spec.id)
    remote_argv = list(plan.argv[1:])
    cmd = [
        "docker",
        "compose",
        "-f",
        str(compose),
        "exec",
        "-T",
        service,
        *remote_argv,
    ]
    return tuple(cmd)


def run_docker_drive(request: ShellDriveRequest, plan: ShellDrivePlan) -> ShellDriveResult:
    from tillm.controller import ShellDriveResult, _timeout_value

    argv = _docker_argv(plan)
    if request.dry_run or not request.execute:
        return ShellDriveResult(
            ok=True,
            client_id=plan.spec.id,
            command=argv,
            prompt_path=plan.prompt_path,
            executed=False,
            dry_run=True,
            execute_profile=plan.execute_profile,
            message="dry-run: docker command planned but not executed",
        )

    try:
        proc = subprocess.run(
            list(argv),
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
            command=argv,
            prompt_path=plan.prompt_path,
            executed=True,
            dry_run=False,
            execute_profile=plan.execute_profile,
            exit_code=None,
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
            message=f"timeout after {request.timeout_seconds}s",
        )
    except OSError as exc:
        return ShellDriveResult(
            ok=False,
            client_id=plan.spec.id,
            command=argv,
            prompt_path=plan.prompt_path,
            executed=True,
            dry_run=False,
            execute_profile=plan.execute_profile,
            exit_code=None,
            message=str(exc),
        )

    return ShellDriveResult(
        ok=proc.returncode == 0,
        client_id=plan.spec.id,
        command=argv,
        prompt_path=plan.prompt_path,
        executed=True,
        dry_run=False,
        execute_profile=plan.execute_profile,
        exit_code=proc.returncode,
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
        message="completed" if proc.returncode == 0 else "docker client command failed",
    )
