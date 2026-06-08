"""CLI for mcp2tillm."""

from __future__ import annotations

import argparse
import sys

from mcp2tillm.server import run_server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mcp2tillm")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("serve", help="Start MCP stdio server")
    args = parser.parse_args(argv or sys.argv[1:])
    if args.cmd == "serve":
        run_server()
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
