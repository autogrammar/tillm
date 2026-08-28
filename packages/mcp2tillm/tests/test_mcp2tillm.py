from pathlib import Path

import pytest


def test_create_server() -> None:
    from mcp2tillm.server import create_server

    server = create_server()
    assert server.name == "tillm"


def test_live_execution_is_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    from mcp2tillm.server import _guard_command

    monkeypatch.delenv("TILLM_MCP_ALLOW_EXECUTE", raising=False)
    with pytest.raises(PermissionError, match="TILLM_MCP_ALLOW_EXECUTE"):
        _guard_command('DRIVE CLIENT claude PROMPT "fix it" EXECUTE true')


def test_dry_run_and_explicit_execution_are_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    from mcp2tillm.server import _guard_command

    monkeypatch.delenv("TILLM_MCP_ALLOW_EXECUTE", raising=False)
    _guard_command('DRIVE CLIENT claude PROMPT "fix it"')
    _guard_command('DRIVE CLIENT claude PROMPT "fix it" EXECUTE true DRY_RUN true')
    monkeypatch.setenv("TILLM_MCP_ALLOW_EXECUTE", "true")
    _guard_command('DRIVE CLIENT claude PROMPT "fix it" EXECUTE true')


def test_project_path_is_confined(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from mcp2tillm.server import _guard_command

    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.setenv("TILLM_MCP_PROJECT_ROOT", str(tmp_path))
    _guard_command(f'DRIVE CLIENT claude PROMPT "fix it" PROJECT {project}')
    with pytest.raises(PermissionError, match="TILLM_MCP_PROJECT_ROOT"):
        _guard_command('DRIVE CLIENT claude PROMPT "fix it" PROJECT /tmp/outside')
