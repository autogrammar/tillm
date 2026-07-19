"""Argument-parser construction for the TILLM CLI.

Owns the :func:`_build_parser` definition (the ``argparse`` layout for every
``tillm`` subcommand) and :func:`_normalize_extra_arg_tokens`, the pre-parse
rewriter that lets users pass ``--extra-arg --flag`` in space form. Isolating
this keeps :mod:`tillm.cli` focused on command dispatch and lets the accepted
invocation surface be regression-tested without driving real commands.
"""

from __future__ import annotations

import argparse
from pathlib import Path

_EXTRA_ARG_OPTION = "--extra-arg"


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
            "(permission bypass where supported). Env: TILLM_EXECUTE_PROFILE."
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
    p_models = provider_sub.add_parser(
        "models", help="List the provider's current models (live from its API)."
    )
    p_models.add_argument("provider_id")
    p_models.add_argument("--limit", type=int, default=30)
    p_models.add_argument("--format", choices=("text", "json"), default="text")
    p_doctor = provider_sub.add_parser(
        "doctor", help="Auto-diagnose a provider: token, endpoint, configured model, clients."
    )
    p_doctor.add_argument("provider_id")
    p_doctor.add_argument("--format", choices=("text", "json"), default="text")

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
        help=(
            "Append client CLI arg when --execute; accepts --extra-arg=--flag "
            "and --extra-arg --flag."
        ),
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
