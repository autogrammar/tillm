"""URI → DSL → dispatch."""

from __future__ import annotations

from dsl2tillm import DslResult, dispatch
from uri2tillm.decode import uri_to_dsl


def run_uri(uri: str, *, default_file: str | None = None) -> DslResult:
    line = uri_to_dsl(uri, default_file=default_file)
    return dispatch(line, default_file=default_file)
