"""Tests for the provider registry, token store, and env overlays."""

from __future__ import annotations

import json
import stat

import pytest

from tillm import providers as prov


@pytest.fixture(autouse=True)
def _isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("TILLM_CONFIG_DIR", str(tmp_path / "tillm-config"))
    for spec in prov.iter_provider_specs():
        monkeypatch.delenv(spec.token_env, raising=False)
    monkeypatch.delenv("TILLM_PROVIDER", raising=False)


class TestRegistry:
    def test_known_providers_present(self):
        ids = {s.id for s in prov.iter_provider_specs()}
        assert {"anthropic", "z.ai", "openrouter", "openai"} <= ids

    def test_alias_resolution(self):
        assert prov.normalize_provider_id("zai") == "z.ai"
        assert prov.normalize_provider_id("GLM") == "z.ai"
        assert prov.normalize_provider_id("or") == "openrouter"

    def test_unknown_provider_raises(self):
        with pytest.raises(prov.UnknownProviderError):
            prov.get_provider_spec("nope")

    def test_zai_compatible_with_claude_code_and_aider(self):
        spec = prov.get_provider_spec("z.ai")
        assert "claude-code" in spec.compatible_clients()
        assert "aider" in spec.compatible_clients()

    def test_openrouter_not_compatible_with_claude_code(self):
        spec = prov.get_provider_spec("openrouter")
        assert "claude-code" not in spec.compatible_clients()


class TestTokenStore:
    def test_save_and_resolve_roundtrip(self):
        path = prov.save_provider_token("z.ai", "sk-test-123", model="glm-4.7")
        assert prov.resolve_provider_token("z.ai") == "sk-test-123"
        assert prov.provider_default_model("z.ai") == "glm-4.7"
        mode = stat.S_IMODE(path.stat().st_mode)
        assert mode == 0o600, f"token store must be 0600, got {oct(mode)}"

    def test_env_var_wins_over_store(self, monkeypatch):
        prov.save_provider_token("z.ai", "stored-token")
        monkeypatch.setenv("ZAI_API_KEY", "env-token")
        assert prov.resolve_provider_token("z.ai") == "env-token"

    def test_store_is_valid_json_per_provider(self):
        prov.save_provider_token("z.ai", "a")
        prov.save_provider_token("openrouter", "b")
        data = json.loads(prov._config_path().read_text())
        assert data["z.ai"]["token"] == "a"
        assert data["openrouter"]["token"] == "b"


class TestEnvOverlay:
    def test_claude_code_via_zai(self):
        prov.save_provider_token("z.ai", "sk-zai")
        overlay = prov.provider_env_overlay("claude-code", "z.ai")
        assert overlay["ANTHROPIC_BASE_URL"] == "https://api.z.ai/api/anthropic"
        assert overlay["ANTHROPIC_AUTH_TOKEN"] == "sk-zai"
        assert overlay["ANTHROPIC_MODEL"] == "glm-4.7"

    def test_aider_via_zai_uses_openai_protocol(self):
        prov.save_provider_token("z.ai", "sk-zai")
        overlay = prov.provider_env_overlay("aider", "z.ai")
        assert overlay["OPENAI_API_KEY"] == "sk-zai"
        assert overlay["OPENAI_API_BASE"].startswith("https://api.z.ai/")

    def test_aider_via_openrouter(self):
        prov.save_provider_token("openrouter", "sk-or")
        overlay = prov.provider_env_overlay("aider", "openrouter")
        assert overlay["OPENAI_API_BASE"] == "https://openrouter.ai/api/v1"

    def test_claude_code_via_openrouter_rejected(self):
        prov.save_provider_token("openrouter", "sk-or")
        with pytest.raises(ValueError, match="protocol"):
            prov.provider_env_overlay("claude-code", "openrouter")

    def test_api_provider_without_token_rejected(self):
        with pytest.raises(ValueError, match="no token"):
            prov.provider_env_overlay("claude-code", "z.ai")

    def test_unmapped_client_rejected(self):
        with pytest.raises(ValueError, match="no provider protocol"):
            prov.provider_env_overlay("gemini-cli", "z.ai")


class TestRequestProviderResolution:
    def test_explicit_wins(self, monkeypatch):
        monkeypatch.setenv("TILLM_PROVIDER", "openrouter")
        assert prov.resolve_request_provider("zai") == "z.ai"

    def test_env_fallback(self, monkeypatch):
        monkeypatch.setenv("TILLM_PROVIDER", "zai")
        assert prov.resolve_request_provider(None) == "z.ai"

    def test_none_when_unset(self):
        assert prov.resolve_request_provider(None) is None


class TestDrivePlanIntegration:
    def test_plan_carries_provider_overlay(self, tmp_path, monkeypatch):
        from tillm.controller import ShellDriveRequest, build_drive_plan

        prov.save_provider_token("z.ai", "sk-zai")
        monkeypatch.setattr(
            "tillm.controller._resolve_command", lambda spec: "/usr/bin/claude"
        )
        request = ShellDriveRequest(
            client_id="claude-code",
            prompt="hello",
            project=tmp_path,
            provider="z.ai",
        )
        plan = build_drive_plan(request)
        assert plan.env_overlay["ANTHROPIC_BASE_URL"] == "https://api.z.ai/api/anthropic"
        assert plan.env_overlay["ANTHROPIC_AUTH_TOKEN"] == "sk-zai"

    def test_plan_no_provider_no_overlay(self, tmp_path, monkeypatch):
        from tillm.controller import ShellDriveRequest, build_drive_plan

        monkeypatch.setattr(
            "tillm.controller._resolve_command", lambda spec: "/usr/bin/claude"
        )
        plan = build_drive_plan(
            ShellDriveRequest(client_id="claude-code", prompt="x", project=tmp_path)
        )
        assert plan.env_overlay == {}


class TestProbe:
    def test_probe_without_token_fails_fast(self):
        result = prov.probe_provider("z.ai")
        assert result.ok is False
        assert "no token" in result.detail

    def test_probe_anthropic_endpoint_success(self, monkeypatch):
        prov.save_provider_token("z.ai", "sk-zai")
        calls: list[str] = []

        def fake_http(url, **kwargs):
            calls.append(url)
            return 200, '{"content": [{"text": "ok"}]}'

        monkeypatch.setattr(prov, "_http_json", fake_http)
        result = prov.probe_provider("z.ai")
        assert result.ok is True
        assert result.model == "glm-4.7"
        assert calls and "api.z.ai/api/anthropic" in calls[0]

    def test_probe_auth_rejection_reported(self, monkeypatch):
        prov.save_provider_token("z.ai", "bad")
        monkeypatch.setattr(prov, "_http_json", lambda *a, **k: (401, "unauthorized"))
        result = prov.probe_provider("z.ai")
        assert result.ok is False
        assert "auth rejected" in result.detail

    def test_probe_model_fallback(self, monkeypatch):
        prov.save_provider_token("z.ai", "sk")
        responses = iter([(404, "model not found"), (200, "ok")])
        monkeypatch.setattr(prov, "_http_json", lambda *a, **k: next(responses))
        result = prov.probe_provider("z.ai")
        assert result.ok is True
        assert result.model == "glm-4.6"


class TestImplicitProviderSafety:
    """A stored default / env provider must never break unmapped clients."""

    def test_stored_default_skips_unmapped_client(self, tmp_path, monkeypatch):
        from tillm.controller import ShellDriveRequest, build_drive_plan

        prov.save_provider_token("z.ai", "sk")
        prov.set_default_provider("z.ai")
        monkeypatch.setattr(
            "tillm.controller._resolve_command", lambda spec: "/usr/bin/gemini"
        )
        plan = build_drive_plan(
            ShellDriveRequest(client_id="gemini-cli", prompt="x", project=tmp_path)
        )
        assert plan.env_overlay == {}  # implicit provider skipped, no crash

    def test_stored_default_applies_to_compatible_client(self, tmp_path, monkeypatch):
        from tillm.controller import ShellDriveRequest, build_drive_plan

        prov.save_provider_token("z.ai", "sk")
        prov.set_default_provider("z.ai")
        monkeypatch.setattr(
            "tillm.controller._resolve_command", lambda spec: "/usr/bin/claude"
        )
        plan = build_drive_plan(
            ShellDriveRequest(client_id="claude-code", prompt="x", project=tmp_path)
        )
        assert plan.env_overlay["ANTHROPIC_AUTH_TOKEN"] == "sk"

    def test_explicit_provider_still_raises_for_unmapped_client(
        self, tmp_path, monkeypatch
    ):
        from tillm.controller import ShellDriveRequest, build_drive_plan

        prov.save_provider_token("z.ai", "sk")
        monkeypatch.setattr(
            "tillm.controller._resolve_command", lambda spec: "/usr/bin/gemini"
        )
        with pytest.raises(ValueError, match="no provider protocol"):
            build_drive_plan(
                ShellDriveRequest(
                    client_id="gemini-cli", prompt="x", project=tmp_path, provider="z.ai"
                )
            )
