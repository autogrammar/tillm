"""CLI for SILLM shell-client control."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tillm.controller import ShellDriveRequest, drive_shell_llm, result_from_error
from tillm.nlp import intent_from_text
from tillm.registry import detect_clients
from tillm.validation import ecosystem_status, validate_intent

_EXTRA_ARG_OPTION = "--extra-arg"


def _print(payload: dict[str, object] | list[dict[str, object]], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if isinstance(payload, list):
        for row in payload:
            mark = "ok" if row.get("available") else "--"
            print(f"{mark} {row.get('id'):<14} {row.get('label')} ({row.get('prompt_mode')})")
        return
    for key, value in payload.items():
        print(f"{key}: {value}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tillm")
    sub = parser.add_subparsers(dest="action", required=True)

    clients = sub.add_parser("clients", help="List registered shell LLM clients.")
    clients.add_argument("--format", choices=("text", "json"), default="text")

    drive = sub.add_parser("drive", help="Build or execute a shell LLM invocation.")
    drive.add_argument("--client", required=True, help="Client id, e.g. aider or claude-code.")
    drive.add_argument("--project", type=Path, default=Path.cwd(), help="Project root.")
    drive.add_argument("--prompt", default=None, help="Prompt text.")
    drive.add_argument("--prompt-file", type=Path, default=None, help="Read prompt text from file.")
    drive.add_argument("--execute", action="store_true", help="Actually run the shell client.")
    drive.add_argument("--dry-run", action="store_true", help="Plan only.")
    drive.add_argument("--timeout", type=float, default=900.0, help="Execution timeout seconds.")
    drive.add_argument(
        "--extra-arg",
        action="append",
        default=[],
        metavar="ARG",
        help="Append client CLI arg; accepts --extra-arg=--flag and --extra-arg --flag.",
    )
    drive.add_argument("--format", choices=("text", "json"), default="json")

    nlp = sub.add_parser("nlp", help="Map natural language to SILLM drive DSL.")
    nlp.add_argument("text", nargs="+", help="Natural-language control request.")
    nlp.add_argument("--client", default=None, help="Default client when text does not name one.")
    nlp.add_argument("--project", type=Path, default=Path.cwd(), help="Project root.")
    nlp.add_argument("--execute", action="store_true", help="Run the inferred client command.")
    nlp.add_argument(
        "--extra-arg",
        action="append",
        default=[],
        metavar="ARG",
        help="Append client CLI arg when --execute; accepts --extra-arg=--flag and --extra-arg --flag.",
    )
    nlp.add_argument("--format", choices=("text", "json"), default="json")

    validate = sub.add_parser("validate", help="Validate SILLM ecosystem hooks.")
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


def _read_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file is not None:
        return args.prompt_file.read_text(encoding="utf-8")
    if args.prompt is not None:
        return args.prompt
    data = sys.stdin.read()
    if data.strip():
        return data
    raise ValueError("missing prompt; use --prompt, --prompt-file, or stdin")


def _drive(args: argparse.Namespace) -> int:
    try:
        result = drive_shell_llm(
            ShellDriveRequest(
                client_id=args.client,
                prompt=_read_prompt(args),
                project=args.project,
                execute=bool(args.execute),
                dry_run=bool(args.dry_run or not args.execute),
                extra_args=tuple(args.extra_arg or ()),
                timeout_seconds=args.timeout,
            )
        )
        payload = result.to_dict()
    except Exception as exc:
        payload = result_from_error(args.client, exc)
        _print(payload, args.format)
        return 2
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
        )
    )
    _print({"ok": result.ok, "source": intent.source, "result": result.to_dict()}, args.format)
    return 0 if result.ok else 1


def main(argv: list[str] | None = None) -> int:
    parse_argv = sys.argv[1:] if argv is None else argv
    args = _build_parser().parse_args(_normalize_extra_arg_tokens(list(parse_argv)))
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
