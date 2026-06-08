"""Query and command handlers delegating to tillm core."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class HandlerResult:
    ok: bool
    output: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "output": self.output, "data": self.data, "error": self.error}


def run_query(payload: dict[str, Any], *, workdir: Path, default_file: str | None = None) -> HandlerResult:
    verb = str(payload["verb"]).upper()
    if verb == "HEALTH":
        return _health()
    if verb == "CLIENTS":
        return _clients()
    if verb == "ORIENT":
        return _orient()
    if verb == "ACTIONS":
        return _actions()
    if verb == "VALIDATE":
        return _validate(payload)
    if verb == "RESOLVE":
        return _resolve(payload)
    if verb == "DOCKER_STATUS":
        return _docker_status()
    return HandlerResult(ok=False, error=f"unknown query verb: {verb}")


def run_command(
    payload: dict[str, Any],
    *,
    workdir: Path,
    default_file: str | None = None,
) -> HandlerResult:
    verb = str(payload["verb"]).upper()
    if verb == "DRIVE":
        return _drive(payload, workdir=workdir)
    if verb == "DRIVE_MATRIX":
        return _drive_matrix(payload, workdir=workdir)
    return HandlerResult(ok=False, error=f"unknown command verb: {verb}")


def _health() -> HandlerResult:
    from tillm.validation import ecosystem_status

    data = ecosystem_status()
    return HandlerResult(ok=True, output=json.dumps(data, indent=2), data=data)


def _clients() -> HandlerResult:
    from tillm.registry import detect_clients

    rows = detect_clients()
    return HandlerResult(ok=True, output=json.dumps(rows, indent=2), data={"clients": rows})


def _orient() -> HandlerResult:
    from tillm.registry import detect_clients

    rows = detect_clients()
    data = {
        "backend": os.getenv("TILLM_BACKEND", "binary"),
        "compose_file": os.getenv("TILLM_COMPOSE_FILE", ""),
        "clients": rows,
    }
    return HandlerResult(ok=True, output=json.dumps(data, indent=2), data=data)


def _actions() -> HandlerResult:
    from tillm.validation import SLLM_DRIVE_ACTIONS

    data = {"actions": sorted(SLLM_DRIVE_ACTIONS), "verbs": ["DRIVE", "DRIVE_MATRIX"]}
    return HandlerResult(ok=True, output=json.dumps(data, indent=2), data=data)


def _validate(payload: dict[str, Any]) -> HandlerResult:
    from tillm.validation import ecosystem_status, validate_client_readiness

    client = payload.get("client")
    if client:
        result = validate_client_readiness(str(client))
        data = result.to_dict()
        return HandlerResult(ok=result.ok, output=json.dumps(data, indent=2), data=data, error=data["errors"][0] if data["errors"] else None)
    data = ecosystem_status()
    return HandlerResult(ok=bool(data.get("ok")), output=json.dumps(data, indent=2), data=data)


def _resolve(payload: dict[str, Any]) -> HandlerResult:
    from nlp2tillm.to_dsl import to_dsl

    prompt = str(payload.get("prompt", ""))
    try:
        line = to_dsl(prompt)
    except Exception as exc:
        return HandlerResult(ok=False, error=str(exc))
    return HandlerResult(ok=True, output=line, data={"dsl": line, "prompt": prompt})


def _docker_status() -> HandlerResult:
    from tillm.transports.docker import docker_service_status

    rows = docker_service_status()
    ok = bool(rows) and "error" not in rows[0]
    return HandlerResult(ok=ok, output=json.dumps(rows, indent=2), data={"services": rows})


def _drive(payload: dict[str, Any], *, workdir: Path) -> HandlerResult:
    from tillm.controller import ShellDriveRequest, drive_shell_llm

    project = Path(str(payload.get("project") or workdir))
    result = drive_shell_llm(
        ShellDriveRequest(
            client_id=str(payload["client"]),
            prompt=str(payload["prompt"]),
            project=project,
            execute=bool(payload.get("execute", False)),
            dry_run=bool(payload.get("dry_run", not payload.get("execute", False))),
            execute_profile=str(payload.get("profile", "default")),
            backend=str(payload.get("backend", "binary")),  # type: ignore[arg-type]
        )
    )
    data = result.to_dict()
    return HandlerResult(
        ok=result.ok,
        output=json.dumps(data, indent=2),
        data=data,
        error=None if result.ok else result.message,
    )


def _drive_matrix(payload: dict[str, Any], *, workdir: Path) -> HandlerResult:
    from tillm.controller import MultiShellDriveRequest, drive_shell_llm_many
    from tillm.registry import resolve_client_ids

    project = Path(str(payload.get("project") or workdir))
    if payload.get("all_clients"):
        client_ids = resolve_client_ids(all_clients=True, available_only=bool(payload.get("available_only", True)))
    else:
        client_ids = resolve_client_ids(
            clients=str(payload.get("clients", "")),
            available_only=bool(payload.get("available_only", True)),
        )
    matrix = drive_shell_llm_many(
        MultiShellDriveRequest(
            client_ids=client_ids,
            prompt=str(payload["prompt"]),
            project=project,
            execute=bool(payload.get("execute", False)),
            dry_run=bool(payload.get("dry_run", not payload.get("execute", False))),
            execute_profile=str(payload.get("profile", "default")),
            parallel=int(payload.get("parallel", 1)),
            fail_fast=bool(payload.get("fail_fast", False)),
            quorum=payload.get("quorum"),
            backend=str(payload.get("backend", "binary")),  # type: ignore[arg-type]
        )
    )
    data = matrix.to_dict()
    return HandlerResult(
        ok=matrix.ok,
        output=json.dumps(data, indent=2),
        data=data,
        error=None if matrix.ok else matrix.message,
    )
