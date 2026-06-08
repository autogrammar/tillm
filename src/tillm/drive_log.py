"""Structured drive logs under <project>/.tillm/logs/."""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def tillm_dir(project: Path) -> Path:
    override = os.getenv("TILLM_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return project.resolve() / ".tillm"


def log_dir(project: Path) -> Path:
    return tillm_dir(project) / "logs"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def append_log(project: Path, event: dict[str, Any]) -> Path:
    """Append one JSON line to the daily drive log."""
    root = log_dir(project)
    root.mkdir(parents=True, exist_ok=True)
    day = time.strftime("%Y%m%d", time.gmtime())
    path = root / f"drive-{day}.jsonl"
    payload = {"ts": _now_iso(), **event}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    latest = root / "latest.json"
    latest.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def log_drive_event(
    project: Path,
    *,
    phase: str,
    client_id: str,
    execute: bool,
    dry_run: bool,
    prompt: str | None = None,
    prompt_path: str | None = None,
    command: list[str] | None = None,
    ok: bool | None = None,
    exit_code: int | None = None,
    message: str = "",
    error: str | None = None,
    duration_ms: int | None = None,
) -> Path:
    event: dict[str, Any] = {
        "phase": phase,
        "client_id": client_id,
        "execute": execute,
        "dry_run": dry_run,
    }
    if prompt is not None:
        text = prompt.strip()
        event["prompt_chars"] = len(text)
        event["prompt_preview"] = text[:240] + ("…" if len(text) > 240 else "")
    if prompt_path is not None:
        event["prompt_path"] = prompt_path
    if command is not None:
        event["command"] = command
    if ok is not None:
        event["ok"] = ok
    if exit_code is not None:
        event["exit_code"] = exit_code
    if message:
        event["message"] = message
    if error is not None:
        event["error"] = error
    if duration_ms is not None:
        event["duration_ms"] = duration_ms
    return append_log(project, event)
