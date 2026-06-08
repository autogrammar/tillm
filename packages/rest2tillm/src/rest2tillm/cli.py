"""CLI for rest2tillm."""

from __future__ import annotations

import argparse
import sys

import uvicorn

from rest2tillm.app import DEFAULT_PORT, create_app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rest2tillm")
    sub = parser.add_subparsers(dest="cmd", required=True)
    serve = sub.add_parser("serve", help="Start REST server")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args(argv or sys.argv[1:])
    if args.cmd == "serve":
        uvicorn.run(create_app(), host=args.host, port=args.port)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
