"""Output-rendering layer for the TILLM CLI.

All presentation concerns for ``tillm`` commands live here: client/matrix row
formatting, drive-result summarisation (the compact ``summary`` format that
strips full client stdout), and the ``_print`` dispatcher that selects between
``text``, ``json`` and ``summary`` output. These helpers are pure functions of
their payload arguments, which keeps them easy to regression-test in isolation
from the command handlers in :mod:`tillm.cli`.
"""

from __future__ import annotations

import json

_SUMMARY_PREVIEW_CHARS = 200


def _format_client_row(row: dict[str, object]) -> str:
    mark = "ok" if row.get("ready") else ("~" if row.get("available") else "--")
    aliases = ", ".join(str(alias) for alias in row.get("aliases", [])) or "-"
    caps = []
    if row.get("supports_execute"):
        caps.append("execute")
    if row.get("supports_dry_run"):
        caps.append("dry-run")
    commands = row.get("commands")
    fallback = commands[0] if isinstance(commands, list) and commands else "?"
    command = row.get("command_path") or fallback
    profiles = row.get("supported_execute_profiles")
    profile_text = (
        ",".join(str(item) for item in profiles) if isinstance(profiles, list) else "default"
    )
    transport = row.get("transport", "binary")
    return (
        f"{mark} {row.get('id'):<14} {row.get('label'):<12} "
        f"mode={row.get('prompt_mode'):<13} caps={','.join(caps) or '-':<12} "
        f"profiles={profile_text:<16} transport={transport:<6} "
        f"cmd={command} aliases={aliases}"
    )


def _format_matrix_row(result: dict[str, object]) -> str:
    status = "ok" if result.get("ok") else "fail"
    exit_code = result.get("exit_code")
    exit_text = "-" if exit_code is None else str(exit_code)
    message = str(result.get("message") or "")
    if len(message) > 48:
        message = message[:45] + "..."
    return (
        f"{status:<4} {str(result.get('client_id')):<14} "
        f"exit={exit_text:<4} dry_run={str(result.get('dry_run')):<5} {message}"
    )


def _output_stats(text: str) -> tuple[int, str]:
    raw = text or ""
    cleaned = raw.strip()
    if not cleaned:
        return len(raw), ""
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    preview = lines[-1] if lines else cleaned
    if len(preview) > _SUMMARY_PREVIEW_CHARS:
        preview = preview[: _SUMMARY_PREVIEW_CHARS - 1] + "…"
    return len(raw), preview


def _summarize_drive_result(row: dict[str, object]) -> dict[str, object]:
    stdout_chars, stdout_preview = _output_stats(str(row.get("stdout") or ""))
    stderr_chars, stderr_preview = _output_stats(str(row.get("stderr") or ""))
    summary: dict[str, object] = {
        key: row[key]
        for key in (
            "ok",
            "client_id",
            "exit_code",
            "message",
            "executed",
            "dry_run",
            "execute_profile",
            "prompt_path",
            "backend",
            "error",
        )
        if key in row
    }
    command = row.get("command")
    if command:
        summary["command"] = command
    if stdout_chars:
        summary["stdout_chars"] = stdout_chars
        if stdout_preview:
            summary["stdout_preview"] = stdout_preview
    if stderr_chars:
        summary["stderr_chars"] = stderr_chars
        if stderr_preview:
            summary["stderr_preview"] = stderr_preview
    return summary


def _summarize_drive_payload(payload: dict[str, object]) -> dict[str, object]:
    if "results" in payload and isinstance(payload["results"], list):
        summarized = dict(payload)
        summarized["results"] = [
            _summarize_drive_result(row) for row in payload["results"] if isinstance(row, dict)
        ]
        return summarized
    if "result" in payload and isinstance(payload["result"], dict):
        summarized = dict(payload)
        summarized["result"] = _summarize_drive_result(payload["result"])
        return summarized
    if "client_id" in payload or "command" in payload:
        return _summarize_drive_result(payload)
    return payload


def _format_drive_summary_line(row: dict[str, object]) -> str:
    status = "ok" if row.get("ok") else "fail"
    exit_code = row.get("exit_code")
    exit_text = "-" if exit_code is None else str(exit_code)
    line = (
        f"{status:<4} {str(row.get('client_id', '?')):<14} "
        f"exit={exit_text:<4} message={row.get('message', '')}"
    )
    extras: list[str] = []
    if row.get("stdout_chars"):
        extras.append(f"stdout_chars={row['stdout_chars']}")
    if row.get("stdout_preview"):
        extras.append(f"stdout_preview={row['stdout_preview']!r}")
    if row.get("stderr_preview"):
        extras.append(f"stderr_preview={row['stderr_preview']!r}")
    if row.get("prompt_path"):
        extras.append(f"prompt_path={row['prompt_path']}")
    if row.get("error"):
        extras.append(f"error={row['error']}")
    if extras:
        line = f"{line} {' '.join(extras)}"
    return line


def _print_summary(payload: dict[str, object] | list[dict[str, object]]) -> None:
    if isinstance(payload, list):
        for row in payload:
            if isinstance(row, dict):
                print(_format_client_row(row))
        return

    summarized = _summarize_drive_payload(payload)
    if "results" in summarized and isinstance(summarized["results"], list):
        print(
            f"matrix ok={summarized.get('ok')} succeeded={summarized.get('succeeded')} "
            f"failed={summarized.get('failed')} message={summarized.get('message')}"
        )
        for row in summarized["results"]:
            if isinstance(row, dict):
                print(_format_drive_summary_line(row))
        return

    if "result" in summarized and isinstance(summarized["result"], dict):
        print(_format_drive_summary_line(summarized["result"]))
        if summarized.get("source"):
            print(f"source={summarized['source']}")
        return

    if isinstance(summarized, dict) and (
        "client_id" in summarized or "command" in summarized or "error" in summarized
    ):
        print(_format_drive_summary_line(summarized))
        return

    for key, value in summarized.items():
        print(f"{key}: {value}")


def _print(payload: dict[str, object] | list[dict[str, object]], output_format: str) -> None:
    if output_format == "summary":
        _print_summary(payload)
        return
    if output_format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if isinstance(payload, list):
        for row in payload:
            print(_format_client_row(row))
        return
    if "results" in payload and isinstance(payload["results"], list):
        print(
            f"matrix ok={payload.get('ok')} succeeded={payload.get('succeeded')} "
            f"failed={payload.get('failed')} message={payload.get('message')}"
        )
        for row in payload["results"]:
            if isinstance(row, dict):
                print(_format_matrix_row(row))
        return
    if "clients" in payload and isinstance(payload["clients"], dict):
        clients = payload["clients"]
        rows = clients.get("rows")
        if isinstance(rows, list):
            print(f"registered: {clients.get('count', len(rows))}")
            for row in rows:
                if isinstance(row, dict):
                    print(_format_client_row(row))
            errors = clients.get("errors")
            if isinstance(errors, list) and errors:
                print("issues:")
                for error in errors:
                    print(f"  - {error}")
            return
    for key, value in payload.items():
        print(f"{key}: {value}")
