"""FastMCP server for dsl2tillm."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


def _enabled(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in _TRUE_VALUES


def _project_root() -> Path:
    return Path(os.getenv("TILLM_MCP_PROJECT_ROOT", ".")).expanduser().resolve()


def _require_within_project_root(raw_path: str) -> None:
    candidate = Path(raw_path).expanduser().resolve(strict=False)
    try:
        candidate.relative_to(_project_root())
    except ValueError as exc:
        raise PermissionError(
            "tillm MCP project path is outside TILLM_MCP_PROJECT_ROOT"
        ) from exc


def _guard_payload(payload: dict[str, Any], *, default_file: str = "") -> None:
    verb = str(payload.get("verb", "")).upper()
    if verb not in {"DRIVE", "DRIVE_MATRIX"}:
        return

    project = str(payload.get("project") or default_file or "")
    if project:
        _require_within_project_root(project)

    live_execution = bool(payload.get("execute", False)) and not bool(
        payload.get("dry_run", False)
    )
    if live_execution and not _enabled("TILLM_MCP_ALLOW_EXECUTE"):
        raise PermissionError(
            "live tillm execution through MCP is disabled; "
            "omit EXECUTE true or set TILLM_MCP_ALLOW_EXECUTE=1"
        )


def _guard_command(command: str | bytes, *, default_file: str = "") -> None:
    from dsl2tillm.codec import envelope_from_bytes, parse_text

    payload = envelope_from_bytes(command) if isinstance(command, bytes) else parse_text(
        command, default_file=default_file or None
    )
    if payload:
        _guard_payload(payload, default_file=default_file)


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
            _guard_command(command, default_file=default_file)
            return dispatch(command, default_file=default_file or None).to_dict()

        @self.app.tool()
        def tillm_run_dsl(script: str, default_file: str = "") -> list[dict[str, Any]]:
            """Execute multiline dsl2tillm script."""
            for line in script.splitlines():
                if line.strip() and not line.lstrip().startswith("#"):
                    _guard_command(line, default_file=default_file)
            return [r.to_dict() for r in execute_dsl(script, default_file=default_file or None)]

        @self.app.tool()
        def tillm_run_command_pb(envelope_bytes: bytes, default_file: str = "") -> bytes:
            """Execute JSON envelope bytes; returns JSON DslResult bytes."""
            _guard_command(envelope_bytes, default_file=default_file)
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
