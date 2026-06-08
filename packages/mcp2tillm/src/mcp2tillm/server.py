"""FastMCP server for dsl2tillm."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _require_fastmcp():
    try:
        from mcp.server.fastmcp import FastMCP
        return FastMCP
    except ImportError as exc:
        raise RuntimeError("Install mcp: pip install mcp") from exc


@dataclass
class TillmMCPServer:
    name: str = "tillm"

    def __post_init__(self) -> None:
        FastMCP = _require_fastmcp()
        self.app = FastMCP(self.name)
        self._register_tools()

    def _register_tools(self) -> None:
        from dsl2tillm.bus import dispatch, execute_dsl
        from dsl2tillm.pb_codec import encode_result_protobuf
        from nlp2tillm.to_dsl import to_dsl

        @self.app.tool()
        def tillm_run_command(command: str, default_file: str = "") -> dict[str, Any]:
            """Execute one dsl2tillm command line."""
            return dispatch(command, default_file=default_file or None).to_dict()

        @self.app.tool()
        def tillm_run_dsl(script: str, default_file: str = "") -> list[dict[str, Any]]:
            """Execute multiline dsl2tillm script."""
            return [r.to_dict() for r in execute_dsl(script, default_file=default_file or None)]

        @self.app.tool()
        def tillm_run_command_pb(envelope_bytes: bytes, default_file: str = "") -> bytes:
            """Execute JSON envelope bytes; returns JSON DslResult bytes."""
            result = dispatch(envelope_bytes, default_file=default_file or None)
            return encode_result_protobuf(result)

        @self.app.tool()
        def tillm_to_dsl(prompt: str, default_file: str = "") -> str:
            """Map natural language to dsl2tillm command line."""
            return to_dsl(prompt, file=default_file or None)

        @self.app.tool()
        def tillm_health() -> dict[str, Any]:
            return dispatch("HEALTH").to_dict()

        @self.app.tool()
        def tillm_clients() -> dict[str, Any]:
            return dispatch("CLIENTS").to_dict()

    def run(self) -> None:
        self.app.run()


def create_server(name: str = "tillm") -> TillmMCPServer:
    return TillmMCPServer(name=name)


def run_server() -> None:
    create_server().run()
