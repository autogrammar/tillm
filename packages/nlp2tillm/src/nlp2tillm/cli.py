"""CLI for nlp2tillm."""

from __future__ import annotations

import argparse
import json
import sys

from nlp2tillm.to_dsl import apply_nl, to_dsl


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nlp2tillm")
    sub = parser.add_subparsers(dest="cmd", required=True)

    to = sub.add_parser("to-dsl", help="Map NL to DSL only")
    to.add_argument("text", nargs="+")
    to.add_argument("--file", default="")

    apply = sub.add_parser("apply", help="Map NL to DSL and dispatch")
    apply.add_argument("text", nargs="+")
    apply.add_argument("--file", default="")
    apply.add_argument("--json", action="store_true")

    args = parser.parse_args(argv or sys.argv[1:])
    text = " ".join(args.text)
    default_file = args.file or None
    if args.cmd == "to-dsl":
        print(to_dsl(text, file=default_file))
        return 0
    payload = apply_nl(text, file=default_file)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(payload.get("output") or payload.get("error"))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
