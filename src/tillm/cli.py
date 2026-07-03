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


_SUMMARY_PREVIEW_CHARS = 200


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
        "--provider",
        default=None,
        help="API provider behind the client (see `tillm providers`), e.g. z.ai.",
    )
    drive.add_argument(
        "--model",
        "--llm",
        dest="model",
        default=None,
        metavar="MODEL",
        help="Force the LLM model via the client's model flag (e.g. sonnet-5).",
    )
    drive.add_argument(
        "--extra-arg",
        action="append",
        default=[],
        metavar="ARG",
        help="Append client CLI arg; accepts --extra-arg=--flag and --extra-arg --flag.",
    )
    drive.add_argument(
        "--format",
        choices=("text", "json", "summary"),
        default="json",
        help="Output format: summary (compact, no full client stdout), json, or text.",
    )

    providers = sub.add_parser(
        "providers", help="List API providers usable behind shell clients."
    )
    providers.add_argument("--format", choices=("text", "json"), default="text")

    provider = sub.add_parser("provider", help="Configure or test a provider.")
    provider_sub = provider.add_subparsers(dest="provider_action", required=True)
    p_set = provider_sub.add_parser("set", help="Store a provider token (chmod 600).")
    p_set.add_argument("provider_id", help="Provider id, e.g. z.ai / openrouter.")
    p_set.add_argument("--token", default=None, help="Token; omit to be prompted.")
    p_set.add_argument("--model", default=None, help="Default model for this provider.")
    p_test = provider_sub.add_parser("test", help="Probe the provider with the stored/env token.")
    p_test.add_argument("provider_id")
    p_test.add_argument("--model", default=None, help="Probe with a specific model.")
    p_test.add_argument("--format", choices=("text", "json"), default="text")

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
        model=args.model,
        provider=args.provider,
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
                    model=args.model,
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


def _providers_list(args: argparse.Namespace) -> int:
    from tillm.providers import iter_provider_specs, resolve_provider_token

    rows = []
    for spec in iter_provider_specs():
        token = resolve_provider_token(spec.id)
        rows.append(
            {
                "id": spec.id,
                "label": spec.label,
                "kind": spec.kind,
                "token": "set" if token else "missing",
                "token_env": spec.token_env,
                "clients": list(spec.compatible_clients()),
                "notes": spec.notes,
            }
        )
    if args.format == "json":
        print(json.dumps(rows, indent=2))
        return 0
    for row in rows:
        token_mark = "✓" if row["token"] == "set" else "✗"
        print(
            f"{row['id']:<12} {row['kind']:<12} token={token_mark} "
            f"({row['token_env']})  clients: {', '.join(row['clients']) or '-'}"
        )
        if row["notes"]:
            print(f"{'':<12} {row['notes']}")
    return 0


def _provider_action(args: argparse.Namespace) -> int:
    from tillm.providers import (
        UnknownProviderError,
        get_provider_spec,
        probe_provider,
        save_provider_token,
    )

    try:
        spec = get_provider_spec(args.provider_id)
    except UnknownProviderError as exc:
        print(f"tillm: {exc}", file=sys.stderr)
        return 2

    if args.provider_action == "set":
        token = (args.token or "").strip()
        if not token:
            import getpass

            token = getpass.getpass(f"{spec.label} token ({spec.token_env}): ").strip()
        if not token:
            print("tillm: empty token, nothing stored", file=sys.stderr)
            return 2
        path = save_provider_token(spec.id, token, model=args.model)
        print(f"✓ stored token for {spec.id} in {path}")
        result = probe_provider(spec.id)
        print(("✓" if result.ok else "✗") + f" probe: {result.detail}")
        return 0 if result.ok else 1

    if args.provider_action == "test":
        result = probe_provider(spec.id, model=args.model)
        if getattr(args, "format", "text") == "json":
            print(json.dumps(result.to_dict(), indent=2))
        else:
            mark = "✓" if result.ok else "✗"
            print(f"{mark} {spec.id}: {result.detail}")
            if result.endpoint:
                print(f"  endpoint: {result.endpoint}")
            if result.attempts:
                print(f"  attempts: {', '.join(result.attempts)}")
        return 0 if result.ok else 1

    raise AssertionError(args.provider_action)


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
    if args.action == "providers":
        return _providers_list(args)
    if args.action == "provider":
        return _provider_action(args)
    if args.action == "nlp":
        return _nlp(args)
    if args.action == "validate":
        _print(ecosystem_status(), args.format)
        return 0
    raise AssertionError(args.action)


if __name__ == "__main__":
    raise SystemExit(main())
