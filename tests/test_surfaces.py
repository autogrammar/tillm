"""Tests for provider config surfaces and `tillm provider sync`."""

from __future__ import annotations

import json
import stat
from pathlib import Path

import pytest

from tillm import providers as prov
from tillm import surfaces as surf

ZAI_ANTHROPIC = "https://api.z.ai/api/anthropic"
ZAI_OPENAI = "https://api.z.ai/api/coding/paas/v4"


@pytest.fixture(autouse=True)
def _sandbox(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("TILLM_CONFIG_DIR", str(tmp_path / ".config" / "tillm"))
    for spec in prov.iter_provider_specs():
        monkeypatch.delenv(spec.token_env, raising=False)
    monkeypatch.delenv("TILLM_PROVIDER", raising=False)
    return tmp_path


def _write_claude_settings(home: Path, *, token: str, extra: dict | None = None) -> Path:
    path = home / ".claude" / "settings.json"
    path.parent.mkdir(parents=True)
    data = dict(extra or {})
    data["env"] = {"ANTHROPIC_BASE_URL": ZAI_ANTHROPIC, "ANTHROPIC_AUTH_TOKEN": token}
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class TestSurfaceStates:
    def test_absent_configs_report_not_present(self):
        for state_dict in surf.plan_sync("z.ai")["states"]:
            assert state_dict["present"] is False
            assert state_dict["configured"] is False

    def test_claude_settings_detected(self, _sandbox):
        _write_claude_settings(_sandbox, token="sk-claude")
        state = surf.ClaudeSettingsSurface().read(prov.get_provider_spec("z.ai"))
        assert state.configured and state.has_token
        assert state.level == "terminal"

    def test_claude_settings_other_provider_not_matched(self, _sandbox):
        _write_claude_settings(_sandbox, token="sk-claude")
        state = surf.ClaudeSettingsSurface().read(prov.get_provider_spec("deepseek"))
        assert state.present and not state.configured and not state.has_token

    def test_jetbrains_xml_detected_read_only(self, _sandbox):
        xml = _sandbox / ".config/JetBrains/PyCharm2026.2/options/llm.provider.openai.like.xml"
        xml.parent.mkdir(parents=True)
        xml.write_text(
            '<application><component name="OpenAILikeLlmProviderSettings">'
            f'<option name="baseUrl" value="{ZAI_OPENAI}" />'
            "</component></application>",
            encoding="utf-8",
        )
        state = surf.JetBrainsOpenAILikeSurface().read(prov.get_provider_spec("z.ai"))
        assert state.configured and state.level == "gui" and not state.writable
        assert state.has_token is False  # key lives in the IDE keychain

    def test_qoder_marker_detection(self, _sandbox):
        xml = _sandbox / ".config/JetBrains/PyCharm2026.2/options/qoder_setting.xml"
        xml.parent.mkdir(parents=True)
        xml.write_text(
            '<application><component name="QoderSettings">'
            '<option name="byokConfigJson" value="glm-5.2 bigmodel" />'
            "</component></application>",
            encoding="utf-8",
        )
        state = surf.QoderSurface().read(prov.get_provider_spec("z.ai"))
        assert state.configured and state.level == "gui" and not state.writable

    def test_qoder_cached_catalog_is_not_configuration(self, _sandbox):
        xml = _sandbox / ".config/JetBrains/PyCharm2026.2/options/qoder_setting.xml"
        xml.parent.mkdir(parents=True)
        xml.write_text(
            '<application><component name="QoderSettings">'
            '<option name="cachedByokConfigJson" value="minimax glm bigmodel moonshot" />'
            "</component></application>",
            encoding="utf-8",
        )
        state = surf.QoderSurface().read(prov.get_provider_spec("z.ai"))
        assert state.present and not state.configured


class TestPlanSync:
    def test_import_planned_when_store_empty_and_claude_has_token(self, _sandbox):
        _write_claude_settings(_sandbox, token="sk-claude")
        plan = surf.plan_sync("z.ai")
        assert plan["store_token"] is False
        actions = {step["surface_id"]: step["action"] for step in plan["steps"]}
        assert actions["claude-settings"] == "import-token"

    def test_plan_is_dry_run(self, _sandbox):
        prov.save_provider_token("z.ai", "sk-stored")
        surf.plan_sync("z.ai")
        assert not (_sandbox / ".claude" / "settings.json").exists()
        assert not (_sandbox / ".codex" / "config.toml").exists()

    def test_exports_planned_when_store_has_token(self):
        prov.save_provider_token("z.ai", "sk-stored")
        actions = {s["surface_id"]: s["action"] for s in surf.plan_sync("z.ai")["steps"]}
        assert actions["claude-settings"] == "export"
        assert actions["codex-config"] == "export"
        assert actions["opencode-config"] == "export"
        assert actions["jetbrains-openai-like"] == "manual"

    def test_level_filter(self):
        prov.save_provider_token("z.ai", "sk-stored")
        gui_only = surf.plan_sync("z.ai", level="gui")
        assert {s["level"] for s in gui_only["states"]} == {"gui"}
        terminal_only = surf.plan_sync("z.ai", level="terminal")
        assert {s["level"] for s in terminal_only["states"]} == {"terminal"}


class TestApplySync:
    def test_import_then_export_in_one_run(self, _sandbox):
        _write_claude_settings(_sandbox, token="sk-claude")
        report = surf.apply_sync("z.ai")
        assert report["store_token"] is True
        assert prov.resolve_provider_token("z.ai") == "sk-claude"
        # the imported token reached the other terminal surfaces
        codex = (_sandbox / ".codex" / "config.toml").read_text(encoding="utf-8")
        assert ZAI_OPENAI in codex and "ZAI_API_KEY" in codex
        opencode = json.loads(
            (_sandbox / ".config/opencode/opencode.json").read_text(encoding="utf-8")
        )
        assert opencode["provider"]["zai"]["options"]["apiKey"] == "sk-claude"

    def test_export_writes_claude_settings_preserving_other_keys(self, _sandbox):
        path = _sandbox / ".claude" / "settings.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"permissions": {"allow": ["Bash(ls:*)"]}}))
        prov.save_provider_token("z.ai", "sk-stored", model="glm-5.2")
        surf.apply_sync("z.ai", level="terminal")
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["permissions"] == {"allow": ["Bash(ls:*)"]}
        assert data["env"]["ANTHROPIC_BASE_URL"] == ZAI_ANTHROPIC
        assert data["env"]["ANTHROPIC_AUTH_TOKEN"] == "sk-stored"
        assert data["env"]["ANTHROPIC_MODEL"] == "glm-5.2"
        assert stat.S_IMODE(path.stat().st_mode) == 0o600

    def test_stale_claude_token_is_refreshed(self, _sandbox):
        _write_claude_settings(_sandbox, token="sk-old")
        prov.save_provider_token("z.ai", "sk-new")
        plan = surf.plan_sync("z.ai")
        actions = {s["surface_id"]: s["action"] for s in plan["steps"]}
        assert actions["claude-settings"] == "export"
        surf.apply_sync("z.ai", level="terminal")
        data = json.loads(
            (_sandbox / ".claude" / "settings.json").read_text(encoding="utf-8")
        )
        assert data["env"]["ANTHROPIC_AUTH_TOKEN"] == "sk-new"

    def test_codex_write_is_idempotent(self):
        spec = prov.get_provider_spec("z.ai")
        surface = surf.CodexConfigSurface()
        surface.write(spec, "sk", None)
        surface.write(spec, "sk", None)
        text = surface._path().read_text(encoding="utf-8")
        assert text.count("[model_providers.zai]") == 1

    def test_second_apply_is_all_ok(self, _sandbox):
        _write_claude_settings(_sandbox, token="sk-claude")
        surf.apply_sync("z.ai")
        report = surf.apply_sync("z.ai", level="terminal")
        assert all(step["action"] == "ok" for step in report["steps"])


class TestSyncAll:
    def test_matrix_covers_providers_with_present_surfaces(self, _sandbox):
        _write_claude_settings(_sandbox, token="sk-claude")
        (_sandbox / ".codex").mkdir()
        (_sandbox / ".codex" / "config.toml").write_text("", encoding="utf-8")
        ids = {report["provider"] for report in surf.sync_all()["providers"]}
        assert {"z.ai", "deepseek", "moonshot", "minimax", "openrouter", "mistral"} <= ids
        assert "anthropic" not in ids  # native subscription — no surface applies

    def test_empty_machine_yields_empty_matrix(self):
        assert surf.sync_all()["providers"] == []

    def test_tokenless_provider_reports_token_url(self, _sandbox):
        _write_claude_settings(_sandbox, token="sk-claude")
        by_id = {report["provider"]: report for report in surf.sync_all()["providers"]}
        assert by_id["minimax"]["store_token"] is False
        assert by_id["minimax"]["token_url"].startswith("https://")

    def test_apply_all_syncs_only_providers_with_tokens(self, _sandbox):
        _write_claude_settings(_sandbox, token="sk-claude")
        matrix = surf.sync_all(apply=True)
        assert prov.resolve_provider_token("z.ai") == "sk-claude"
        # no token materialised out of thin air for the others
        assert prov.resolve_provider_token("minimax") is None
        opencode = json.loads(
            (_sandbox / ".config/opencode/opencode.json").read_text(encoding="utf-8")
        )
        assert list(opencode["provider"]) == ["zai"]


class TestCliSync:
    def test_cli_sync_matrix_no_provider(self, capsys, _sandbox):
        from tillm.cli import main

        _write_claude_settings(_sandbox, token="sk-from-claude")
        prov.save_provider_token("z.ai", "sk-stored")
        code = main(["provider", "sync"])
        out = capsys.readouterr().out
        assert code == 0
        assert "matrix" in out and "z.ai" in out and "minimax" in out
        assert "sk-stored" not in out and "sk-from-claude" not in out
    def test_cli_sync_dry_run_text(self, capsys):
        from tillm.cli import main

        prov.save_provider_token("z.ai", "sk-stored")
        code = main(["provider", "sync", "z.ai", "--level", "terminal"])
        out = capsys.readouterr().out
        assert code == 0
        assert "dry-run" in out and "export" in out
        assert "sk-stored" not in out  # tokens never printed

    def test_cli_sync_apply_json(self, capsys, _sandbox):
        from tillm.cli import main

        _write_claude_settings(_sandbox, token="sk-claude")
        code = main(["provider", "sync", "z.ai", "--format", "json", "--apply"])
        payload = json.loads(capsys.readouterr().out)
        assert code in (0, 1)  # 1 when GUI surfaces report "manual"
        assert payload["store_token"] is True
        assert "sk-claude" not in json.dumps(payload)


class TestSurfaceSelector:
    def test_alias_normalization(self):
        assert surf.normalize_surface_ids(["claude", "codex-config"]) == frozenset(
            {"claude-settings", "codex-config"}
        )
        assert surf.normalize_surface_ids(None) is None
        assert surf.normalize_surface_ids([]) is None

    def test_unknown_surface_raises(self):
        with pytest.raises(surf.UnknownSurfaceError):
            surf.normalize_surface_ids(["notepad"])

    def test_apply_with_surface_filter_leaves_claude_alone(self, _sandbox):
        prov.save_provider_token("z.ai", "sk-stored")
        surf.apply_sync("z.ai", only=frozenset({"codex-config", "opencode-config"}))
        assert not (_sandbox / ".claude" / "settings.json").exists()
        assert (_sandbox / ".codex" / "config.toml").exists()
        assert (_sandbox / ".config/opencode/opencode.json").exists()

    def test_cli_surface_filter(self, capsys, _sandbox):
        from tillm.cli import main

        prov.save_provider_token("z.ai", "sk-stored")
        code = main(
            ["provider", "sync", "z.ai", "--apply", "--surface", "codex", "--surface", "opencode"]
        )
        capsys.readouterr()
        assert code == 0
        assert not (_sandbox / ".claude" / "settings.json").exists()
        assert (_sandbox / ".codex" / "config.toml").exists()

    def test_cli_unknown_surface_is_error(self, capsys):
        from tillm.cli import main

        code = main(["provider", "sync", "z.ai", "--surface", "notepad"])
        assert code == 2
        assert "unknown surface" in capsys.readouterr().err
