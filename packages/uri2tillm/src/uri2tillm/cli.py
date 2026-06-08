"""CLI for uri2tillm."""

from __future__ import annotations

import argparse
import json
import sys

from uri2tillm.decode import uri_to_dsl
from uri2tillm.run import run_uri


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="uri2tillm")
    sub = parser.add_subparsers(dest="cmd", required=True)

    decode = sub.add_parser("decode", help="URI to DSL line")
    decode.add_argument("--uri", required=True)
    decode.add_argument("--file", default="")

    run = sub.add_parser("run", help="URI to dispatch")
    run.add_argument("--uri", required=True)
    run.add_argument("--file", default="")
    run.add_argument("--json", action="store_true")

    args = parser.parse_args(argv or sys.argv[1:])
    default_file = args.file or None
    if args.cmd == "decode":
        print(uri_to_dsl(args.uri, default_file=default_file))
        return 0
    result = run_uri(args.uri, default_file=default_file)
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(result.output or result.error)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
