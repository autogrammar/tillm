"""Text DSL grammar → validated command dict."""

from __future__ import annotations

import shlex
from typing import Any


def _flag(rest: list[str], name: str) -> str | None:
    key = name.upper()
    upper = [token.upper() for token in rest]
    if key in upper:
        idx = upper.index(key)
        if idx + 1 < len(rest):
            return rest[idx + 1]
    return None


def _bool_flag(rest: list[str], name: str) -> bool | None:
    value = _flag(rest, name)
    if value is None:
        return None
    return value.lower() in {"1", "true", "yes", "on"}


def _quoted_or_tail(rest: list[str]) -> str:
    if rest and rest[0].startswith('"'):
        return " ".join(rest).strip('"')
    return " ".join(rest)


def parse_line(line: str, *, default_file: str | None = None) -> dict[str, Any]:
    line = line.strip()
    if not line or line.startswith("#"):
        return {}
    tokens = shlex.split(line, posix=True)
    if not tokens:
        return {}
    verb = tokens[0].upper()
    rest = tokens[1:]
    payload: dict[str, Any] = {"verb": verb}

    if verb in {"HEALTH", "CLIENTS", "ORIENT", "ACTIONS", "DOCKER_STATUS"}:
        return payload

    if verb == "VALIDATE":
        client = _flag(rest, "CLIENT")
        if client:
            payload["client"] = client
        return payload

    if verb == "RESOLVE":
        payload["prompt"] = _quoted_or_tail(rest)
        return payload

    if verb == "DRIVE":
        payload["client"] = _flag(rest, "CLIENT") or ""
        prompt = _flag(rest, "PROMPT")
        if prompt is None and rest:
            prompt = _quoted_or_tail(rest)
        payload["prompt"] = prompt or ""
        execute = _bool_flag(rest, "EXECUTE")
        if execute is not None:
            payload["execute"] = execute
        dry_run = _bool_flag(rest, "DRY_RUN")
        if dry_run is not None:
            payload["dry_run"] = dry_run
        profile = _flag(rest, "PROFILE")
        if profile:
            payload["profile"] = profile
        backend = _flag(rest, "BACKEND")
        if backend:
            payload["backend"] = backend
        project = _flag(rest, "PROJECT") or default_file
        if project:
            payload["project"] = project
        return payload

    if verb == "DRIVE_MATRIX":
        clients = _flag(rest, "CLIENTS")
        if clients:
            payload["clients"] = clients
        if _flag(rest, "ALL") is not None or (rest and rest[0].upper() == "ALL"):
            payload["all_clients"] = True
        prompt = _flag(rest, "PROMPT")
        if prompt is None:
            prompt = _quoted_or_tail(rest)
        payload["prompt"] = prompt or ""
        execute = _bool_flag(rest, "EXECUTE")
        if execute is not None:
            payload["execute"] = execute
        dry_run = _bool_flag(rest, "DRY_RUN")
        if dry_run is not None:
            payload["dry_run"] = dry_run
        profile = _flag(rest, "PROFILE")
        if profile:
            payload["profile"] = profile
        parallel = _flag(rest, "PARALLEL")
        if parallel:
            payload["parallel"] = int(parallel)
        fail_fast = _bool_flag(rest, "FAIL_FAST")
        if fail_fast is not None:
            payload["fail_fast"] = fail_fast
        quorum = _flag(rest, "QUORUM")
        if quorum:
            payload["quorum"] = int(quorum)
        available_only = _bool_flag(rest, "AVAILABLE_ONLY")
        if available_only is not None:
            payload["available_only"] = available_only
        project = _flag(rest, "PROJECT") or default_file
        if project:
            payload["project"] = project
        return payload

    payload["raw"] = rest
    return payload


def to_text(payload: dict[str, Any]) -> str:
    verb = str(payload.get("verb", "")).upper()
    if verb in {"HEALTH", "CLIENTS", "ORIENT", "ACTIONS", "DOCKER_STATUS"}:
        return verb
    if verb == "VALIDATE":
        client = payload.get("client")
        return f"VALIDATE CLIENT {client}" if client else "VALIDATE"
    if verb == "RESOLVE":
        return f'RESOLVE "{payload.get("prompt", "")}"'
    if verb == "DRIVE":
        parts = [f"DRIVE CLIENT {payload.get('client', '')}", f'PROMPT "{payload.get("prompt", "")}"']
        if payload.get("execute"):
            parts.append("EXECUTE true")
        if payload.get("dry_run"):
            parts.append("DRY_RUN true")
        if payload.get("profile"):
            parts.append(f"PROFILE {payload['profile']}")
        if payload.get("backend"):
            parts.append(f"BACKEND {payload['backend']}")
        return " ".join(parts)
    if verb == "DRIVE_MATRIX":
        parts = ["DRIVE_MATRIX"]
        if payload.get("all_clients"):
            parts.append("ALL")
        elif payload.get("clients"):
            parts.append(f"CLIENTS {payload['clients']}")
        parts.append(f'PROMPT "{payload.get("prompt", "")}"')
        if payload.get("parallel"):
            parts.append(f"PARALLEL {payload['parallel']}")
        if payload.get("execute"):
            parts.append("EXECUTE true")
        return " ".join(parts)
    return verb
