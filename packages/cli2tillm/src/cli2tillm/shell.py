"""Interactive REPL for dsl2tillm."""

from __future__ import annotations

import json
import sys

from dsl2tillm.bus import dispatch


def run_shell(*, default_file: str | None = None, json_out: bool = False) -> int:
    print("cli2tillm shell — enter DSL lines, Ctrl-D to exit")
    code = 0
    while True:
        try:
            line = input("tillm> ").strip()
        except EOFError:
            print()
            break
        if not line:
            continue
        result = dispatch(line, default_file=default_file)
        if json_out:
            print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        else:
            if result.error:
                print(f"error: {result.error}", file=sys.stderr)
            if result.output:
                print(result.output.rstrip())
        if not result.ok:
            code = 1
    return code
