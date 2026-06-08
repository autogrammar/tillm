"""CLI for TILLM shell-client control."""

from __future__ import annotations

import argparse
import json
import os
import select
import sys
from pathlib import Path

from tillm.drive_log import log_drive_event
from tillm.project_env import bootstrap_project_env
from tillm.controller import (
    MultiShellDriveRequest,
    ShellDriveRequest,
    drive_shell_llm,
    drive_shell_llm_many,
    result_from_error,
)
from tillm.nlp import intent_from_text
from tillm.registry import DEFAULT_EXECUTE_PROFILE, detect_clients, normalize_execute_profile, resolve_client_ids
from tillm.validation import ecosystem_status, validate_intent

_EXTRA_ARG_OPTION = "--extra-arg"


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
    profile_text = ",".join(str(item) for item in profiles) if isinstance(profiles, list) else "default"
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


def _print(payload: dict[str, object] | list[dict[str, object]], output_format: str) -> None:
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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tillm")
    sub = parser.add_subparsers(dest="action", required=True)

    clients = sub.add_parser("clients", help="List registered shell LLM clients.")
    clients.add_argument("--format", choices=("text", "json"), default="text")

    drive = sub.add_parser("drive", help="Build or execute a shell LLM invocation.")
    target = drive.add_mutually_exclusive_group(required=True)
    target.add_argument("--client", help="Single client id, e.g. aider or claude-code.")
    target.add_argument(
        "--clients",
        help="Comma-separated client ids, e.g. aider,claude-code,codex.",
    )
    target.add_argument(
        "--all",
        action="store_true",
        help="Drive all registered clients (defaults to available-only).",
    )
    drive.add_argument("--project", type=Path, default=Path.cwd(), help="Project root.")
    drive.add_argument(
        "--prompt",
        default=None,
        help="Prompt text (required unless --prompt-file or stdin pipe is used).",
    )
    drive.add_argument("--prompt-file", type=Path, default=None, help="Read prompt text from file.")
    drive.add_argument("--execute", action="store_true", help="Actually run the shell client.")
    drive.add_argument(
        "--profile",
        default=None,
        help=(
            "Execute profile: default (conservative) or automation "
            f"(permission bypass where supported). Env: TILLM_EXECUTE_PROFILE."
        ),
    )
    drive.add_argument("--dry-run", action="store_true", help="Plan only.")
    drive.add_argument(
        "--available-only",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="For --all/--clients, skip clients without a binary in PATH.",
    )
    drive.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="Max concurrent client runs for --all/--clients (default: 1).",
    )
    drive.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop the matrix after the first failed client.",
    )
    drive.add_argument(
        "--quorum",
        type=int,
        default=None,
        help="Stop after this many successful clients.",
    )
    drive.add_argument("--timeout", type=float, default=900.0, help="Execution timeout seconds.")
    drive.add_argument(
        "--extra-arg",
        action="append",
        default=[],
        metavar="ARG",
        help="Append client CLI arg; accepts --extra-arg=--flag and --extra-arg --flag.",
    )
    drive.add_argument("--format", choices=("text", "json"), default="json")

    nlp = sub.add_parser("nlp", help="Map natural language to TILLM drive DSL.")
    nlp.add_argument("text", nargs="+", help="Natural-language control request.")
    nlp.add_argument("--client", default=None, help="Default client when text does not name one.")
    nlp.add_argument("--project", type=Path, default=Path.cwd(), help="Project root.")
    nlp.add_argument("--execute", action="store_true", help="Run the inferred client command.")
    nlp.add_argument(
        "--profile",
        default=None,
        help="Execute profile for --execute (default or automation).",
    )
    nlp.add_argument(
        "--extra-arg",
        action="append",
        default=[],
        metavar="ARG",
        help="Append client CLI arg when --execute; accepts --extra-arg=--flag and --extra-arg --flag.",
    )
    nlp.add_argument("--format", choices=("text", "json"), default="json")

    validate = sub.add_parser("validate", help="Validate TILLM ecosystem hooks.")
    validate.add_argument("--format", choices=("text", "json"), default="json")

    return parser


def _normalize_extra_arg_tokens(argv: list[str]) -> list[str]:
    normalized: list[str] = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == _EXTRA_ARG_OPTION and index + 1 < len(argv):
            value = argv[index + 1]
            if value.startswith("-"):
                normalized.append(f"{_EXTRA_ARG_OPTION}={value}")
                index += 2
                continue
        normalized.append(token)
        index += 1
    return normalized


def _resolve_execute_profile(raw: str | None) -> str:
    return normalize_execute_profile(raw or os.getenv("TILLM_EXECUTE_PROFILE"))


def _missing_prompt_error() -> ValueError:
    return ValueError(
        "missing prompt; provide --prompt, --prompt-file, or pipe text on stdin. "
        "Examples:\n"
        "  tillm drive --client aider --prompt 'Refactor X' --execute\n"
        "  tillm drive --client aider --prompt-file task.md --execute\n"
        "  echo 'Refactor X' | tillm drive --client aider --execute"
    )


def _stdin_has_data() -> bool:
    try:
        return bool(select.select([sys.stdin], [], [], 0)[0])
    except Exception:
        return False


def _read_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file is not None:
        return args.prompt_file.read_text(encoding="utf-8")
    if args.prompt is not None:
        return args.prompt
    if sys.stdin.isatty() or not _stdin_has_data():
        raise _missing_prompt_error()
    data = sys.stdin.read()
    if data.strip():
        return data
    raise _missing_prompt_error()


def _resolve_drive_targets(args: argparse.Namespace) -> tuple[str, ...]:
    return resolve_client_ids(
        client=args.client,
        clients=args.clients,
        all_clients=bool(args.all),
        available_only=bool(args.available_only),
    )


def _base_drive_request(args: argparse.Namespace, prompt: str) -> MultiShellDriveRequest:
    return MultiShellDriveRequest(
        client_ids=_resolve_drive_targets(args),
        prompt=prompt,
        project=args.project,
        execute=bool(args.execute),
        dry_run=bool(args.dry_run or not args.execute),
        extra_args=tuple(args.extra_arg or ()),
        execute_profile=_resolve_execute_profile(args.profile),
        timeout_seconds=args.timeout,
        parallel=max(1, int(args.parallel)),
        fail_fast=bool(args.fail_fast),
        quorum=args.quorum,
    )


def _drive(args: argparse.Namespace) -> int:
    try:
        prompt = _read_prompt(args)
    except ValueError as exc:
        label = args.client or args.clients or "all"
        log_drive_event(
            args.project,
            phase="prompt_error",
            client_id=str(label),
            execute=bool(args.execute),
            dry_run=bool(args.dry_run or not args.execute),
            ok=False,
            error=type(exc).__name__,
            message=str(exc),
        )
        payload = result_from_error(str(label), exc)
        _print(payload, args.format)
        return 2

    client_label = args.client or args.clients or "all"
    log_drive_event(
        args.project,
        phase="start",
        client_id=str(client_label),
        execute=bool(args.execute),
        dry_run=bool(args.dry_run or not args.execute),
        prompt=prompt,
    )
    try:
        if args.client:
            result = drive_shell_llm(
                ShellDriveRequest(
                    client_id=args.client,
                    prompt=prompt,
                    project=args.project,
                    execute=bool(args.execute),
                    dry_run=bool(args.dry_run or not args.execute),
                    extra_args=tuple(args.extra_arg or ()),
                    execute_profile=_resolve_execute_profile(args.profile),
                    timeout_seconds=args.timeout,
                )
            )
            payload: dict[str, object] = result.to_dict()
        else:
            matrix = drive_shell_llm_many(_base_drive_request(args, prompt))
            payload = matrix.to_dict()
    except Exception as exc:
        log_drive_event(
            args.project,
            phase="error",
            client_id=str(client_label),
            execute=bool(args.execute),
            dry_run=bool(args.dry_run or not args.execute),
            prompt=prompt,
            ok=False,
            error=type(exc).__name__,
            message=str(exc),
        )
        payload = result_from_error(str(client_label), exc)
        _print(payload, args.format)
        return 2

    if args.client and isinstance(payload, dict):
        log_drive_event(
            args.project,
            phase="finish",
            client_id=str(payload.get("client_id", client_label)),
            execute=bool(args.execute),
            dry_run=bool(payload.get("dry_run", True)),
            prompt=prompt,
            prompt_path=str(payload.get("prompt_path", "")),
            command=list(payload.get("command", [])) if payload.get("command") else None,
            ok=bool(payload.get("ok")),
            exit_code=payload.get("exit_code"),  # type: ignore[arg-type]
            message=str(payload.get("message", "")),
        )
    _print(payload, args.format)
    return 0 if payload.get("ok") else 1


def _nlp(args: argparse.Namespace) -> int:
    text = " ".join(args.text)
    intent = intent_from_text(text, default_client=args.client)
    validation = validate_intent(intent)
    if not validation.ok:
        payload = {"ok": False, "intent": intent.to_dsl(), "validation": validation.to_dict()}
        _print(payload, args.format)
        return 2
    if not args.execute:
        payload = {"ok": True, "source": intent.source, "dsl": intent.to_dsl()}
        _print(payload, args.format)
        return 0
    result = drive_shell_llm(
        ShellDriveRequest(
            client_id=intent.client_id,
            prompt=intent.prompt,
            project=args.project,
            execute=True,
            dry_run=False,
            extra_args=tuple(args.extra_arg or ()),
            execute_profile=_resolve_execute_profile(args.profile),
        )
    )
    _print({"ok": result.ok, "source": intent.source, "result": result.to_dict()}, args.format)
    return 0 if result.ok else 1


def main(argv: list[str] | None = None) -> int:
    parse_argv = sys.argv[1:] if argv is None else argv
    args = _build_parser().parse_args(_normalize_extra_arg_tokens(list(parse_argv)))
    bootstrap_project_env(Path.cwd())
    if args.action == "clients":
        _print(detect_clients(), args.format)
        return 0
    if args.action == "drive":
        return _drive(args)
    if args.action == "nlp":
        return _nlp(args)
    if args.action == "validate":
        _print(ecosystem_status(), args.format)
        return 0
    raise AssertionError(args.action)


if __name__ == "__main__":
    raise SystemExit(main())
