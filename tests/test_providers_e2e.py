"""End-to-end tests: CLI drive -> plan -> transport -> provider env in the subprocess.

Uses a fake `claude` binary that dumps the ANTHROPIC_* environment it
received, so the full stack is exercised without any network access.
The live-API probe test runs only when a real token is present.
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest

from tillm.cli import main as tillm_main


@pytest.fixture()
def fake_claude(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    script = bin_dir / "claude"
    script.write_text(
        "#!/bin/bash\n"
        'echo "FAKE_CLAUDE_OK base=$ANTHROPIC_BASE_URL '
        'token=$ANTHROPIC_AUTH_TOKEN model=$ANTHROPIC_MODEL"\n'
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.setenv("TILLM_CONFIG_DIR", str(tmp_path / "cfg"))
    project = tmp_path / "proj"
    project.mkdir()
    return project


def _run_cli(capsys, argv):
    rc = tillm_main(argv)
    out = capsys.readouterr().out
    return rc, json.loads(out)


class TestDriveProviderE2E:
    def test_single_client_receives_zai_env(self, fake_claude, capsys, monkeypatch):
        monkeypatch.setenv("ZAI_API_KEY", "sk-e2e")
        rc, result = _run_cli(
            capsys,
            [
                "drive", "--client", "claude-code", "--provider", "z.ai",
                "--prompt", "ping", "--execute",
                "--project", str(fake_claude), "--format", "json",
            ],
        )
        assert rc == 0
        assert result["ok"] is True
        assert "base=https://api.z.ai/api/anthropic" in result["stdout"]
        assert "token=sk-e2e" in result["stdout"]
        assert "model=glm-4.7" in result["stdout"]

    def test_matrix_path_receives_zai_env(self, fake_claude, capsys, monkeypatch):
        monkeypatch.setenv("ZAI_API_KEY", "sk-e2e")
        rc, result = _run_cli(
            capsys,
            [
                "drive", "--clients", "claude-code", "--provider", "z.ai",
                "--prompt", "ping", "--execute",
                "--project", str(fake_claude), "--format", "json",
            ],
        )
        first = result["results"][0]
        assert first["ok"] is True
        assert "token=sk-e2e" in first["stdout"]

    def test_provider_env_var_tillm_provider(self, fake_claude, capsys, monkeypatch):
        monkeypatch.setenv("ZAI_API_KEY", "sk-e2e")
        monkeypatch.setenv("TILLM_PROVIDER", "zai")  # alias, no --provider flag
        rc, result = _run_cli(
            capsys,
            [
                "drive", "--client", "claude-code",
                "--prompt", "ping", "--execute",
                "--project", str(fake_claude), "--format", "json",
            ],
        )
        assert "base=https://api.z.ai/api/anthropic" in result["stdout"]

    def test_missing_token_fails_with_actionable_message(
        self, fake_claude, capsys, monkeypatch
    ):
        monkeypatch.delenv("ZAI_API_KEY", raising=False)
        rc, result = _run_cli(
            capsys,
            [
                "drive", "--client", "claude-code", "--provider", "z.ai",
                "--prompt", "ping", "--execute",
                "--project", str(fake_claude), "--format", "json",
            ],
        )
        assert result["ok"] is False
        assert "tillm provider set z.ai" in result["message"]

    def test_no_provider_no_env_leak(self, fake_claude, capsys, monkeypatch):
        monkeypatch.delenv("TILLM_PROVIDER", raising=False)
        monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
        rc, result = _run_cli(
            capsys,
            [
                "drive", "--client", "claude-code",
                "--prompt", "ping", "--execute",
                "--project", str(fake_claude), "--format", "json",
            ],
        )
        assert result["ok"] is True
        assert "base= " in result["stdout"] or "base=\n" in result["stdout"] or "base= token" in result["stdout"]


@pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY", "").strip(),
    reason="live probe needs OPENROUTER_API_KEY",
)
def test_live_openrouter_probe():
    from tillm.providers import probe_provider

    result = probe_provider("openrouter")
    assert result.ok, result.detail


@pytest.mark.skipif(
    not os.environ.get("ZAI_API_KEY", "").strip(),
    reason="live probe needs ZAI_API_KEY",
)
def test_live_zai_probe():
    from tillm.providers import probe_provider

    result = probe_provider("z.ai")
    assert result.ok, result.detail
