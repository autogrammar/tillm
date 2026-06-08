"""CLI for dsl2tillm."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dsl2tillm.bus import dispatch, execute_dsl
from dsl2tillm.schema_registry import validate_schemas

_SUBCOMMANDS = frozenset({"exec", "run", "validate-schema", "replay"})


def _main_legacy(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="dsl2tillm")
    parser.add_argument("script", nargs="?", help="DSL script or single command")
    parser.add_argument("-c", "--command", default="", help="Single DSL command")
    parser.add_argument("--file", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    default_file = args.file or None
    if args.command:
        result = dispatch(args.command, default_file=default_file)
        print(json.dumps(result.to_dict(), indent=2) if args.json else result.output or result.error)
        return 0 if result.ok else 1
    if args.script:
        results = execute_dsl(Path(args.script).read_text(encoding="utf-8"), default_file=default_file)
        code = 0
        for result in results:
            if args.json:
                print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
            else:
                if result.error:
                    print(f"error: {result.error}", file=sys.stderr)
                if result.output:
                    print(result.output.rstrip())
            if not result.ok:
                code = 1
        return code
    parser.print_help()
    return 1


def _main_subcommand(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="dsl2tillm")
    sub = parser.add_subparsers(dest="cmd", required=True)

    exe = sub.add_parser("exec", help="Execute one DSL command")
    exe.add_argument("command")
    exe.add_argument("--file", default="")
    exe.add_argument("--json", action="store_true")

    run = sub.add_parser("run", help="Run .dsl script")
    run.add_argument("script")
    run.add_argument("--file", default="")
    run.add_argument("--json", action="store_true")

    sub.add_parser("validate-schema", help="Validate JSON schemas")

    replay = sub.add_parser("replay", help="Replay events from jsonl store")
    replay.add_argument("--file", default=".")

    args = parser.parse_args(argv)
    if args.cmd == "validate-schema":
        errors = validate_schemas()
        print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
        return 0 if not errors else 1
    if args.cmd == "replay":
        from dsl2tillm.events import EventStore

        events = EventStore.for_workdir(Path(args.file)).read_all()
        print(json.dumps([event.to_dict() for event in events], indent=2))
        return 0
    default_file = getattr(args, "file", "") or None
    if args.cmd == "exec":
        result = dispatch(args.command, default_file=default_file)
        if args.json:
            print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        else:
            if result.error:
                print(f"error: {result.error}", file=sys.stderr)
            if result.output:
                print(result.output.rstrip())
        return 0 if result.ok else 1
    if args.cmd == "run":
        results = execute_dsl(Path(args.script).read_text(encoding="utf-8"), default_file=default_file)
        code = 0
        for result in results:
            if args.json:
                print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
            else:
                if result.error:
                    print(f"error: {result.error}", file=sys.stderr)
                if result.output:
                    print(result.output.rstrip())
            if not result.ok:
                code = 1
        return code
    return 1


def main(argv: list[str] | None = None) -> int:
    parse_argv = list(argv if argv is not None else sys.argv[1:])
    if parse_argv and parse_argv[0] in _SUBCOMMANDS:
        return _main_subcommand(parse_argv)
    return _main_legacy(parse_argv)


if __name__ == "__main__":
    raise SystemExit(main())
