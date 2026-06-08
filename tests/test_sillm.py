from __future__ import annotations

import json
from pathlib import Path

from tillm.cli import main
from tillm.compat import (
    agent_backend_aliases,
    agent_backend_profiles,
    autopilot_backend_for_client,
    detect_koru_agent_rows,
    is_client_available,
    shell_client_ids,
    shell_process_patterns,
    tool_registry_entries,
)
from tillm.controller import ShellDriveRequest, build_drive_plan
from tillm.nlp import ShellIntent, intent_from_text
from tillm.registry import detect_clients, get_client_spec, normalize_client_id
from tillm.validation import (
    ecosystem_status,
    intent_contracts,
    validate_intent,
    validate_intent_contracts,
)


def test_registry_normalizes_common_aliases() -> None:
    assert normalize_client_id("claude") == "claude-code"
    assert normalize_client_id("codex-cli") == "codex"
    assert get_client_spec("aider") is not None


def test_detect_clients_marks_available_from_injected_which() -> None:
    rows = detect_clients(which=lambda name: f"/bin/{name}" if name == "aider" else None)
    aider = next(row for row in rows if row["id"] == "aider")
    claude = next(row for row in rows if row["id"] == "claude-code")
    assert aider["available"] is True
    assert claude["available"] is False


def test_compat_exports_koru_agent_rows() -> None:
    import shutil
    from unittest.mock import patch

    def fake_which(name: str) -> str | None:
        return "/usr/bin/claude" if name == "claude" else None

    with patch.object(shutil, "which", fake_which):
        rows = detect_koru_agent_rows()
        claude = next(row for row in rows if row["id"] == "claude-code")
        assert "claude-code" in shell_client_ids()

        # Get the autopilot backend constant from the function result
        autopilot_backend = autopilot_backend_for_client("claude")
        assert autopilot_backend is not None

        assert claude["available"] is True
        assert claude["launchable"] is True
        assert claude["command"] == "/usr/bin/claude"
        assert is_client_available("claude") is True
        assert is_client_available("aider") is False
        assert ("codex", "Codex CLI", ("codex",)) in shell_process_patterns()
        registry = {str(row["id"]): row for row in tool_registry_entries()}
        assert registry["aider"]["category"] == "cli_agent"
        assert registry["aider"]["invoke"] == (
            "koru tillm drive --client aider --prompt '<prompt>' --execute"
        )
        assert registry["codex-cli"]["invoke"] == (
            "koru tillm drive --client codex --prompt '<prompt>' --execute"
        )

        # Get backend profile info dynamically
        aliases = agent_backend_aliases()
        profiles = agent_backend_profiles()
        if aliases and "tillm_shell" in aliases and profiles:
            backend_profile_id = aliases["tillm_shell"]
            assert profiles[0]["id"] == backend_profile_id


def test_build_drive_plan_uses_message_file_for_aider(tmp_path: Path) -> None:
    import shutil
    from unittest.mock import patch

    def fake_which(name: str) -> str | None:
        return f"/usr/bin/{name}" if name == "aider" else None

    with patch.object(shutil, "which", fake_which):
        plan = build_drive_plan(
            ShellDriveRequest(
                client_id="aider",
                prompt="Fix PLF-1",
                project=tmp_path,
            )
        )
        assert plan.argv[0] == "/usr/bin/aider"
        assert "--no-show-model-warnings" in plan.argv
        assert "--yes-always" in plan.argv
        assert "--message-file" in plan.argv
        assert plan.prompt_path.exists()
        assert plan.stdin_text is None


def test_drive_cli_accepts_space_form_extra_arg_flags(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    monkeypatch.setattr(
        "shutil.which",
        lambda name: f"/usr/bin/{name}" if name == "aider" else None,
    )

    rc = main(
        [
            "drive",
            "--client",
            "aider",
            "--project",
            str(tmp_path),
            "--prompt",
            "Fix tests",
            "--extra-arg",
            "--no-show-model-warnings",
            "--extra-arg",
            "--yes-always",
            "--format",
            "json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["ok"] is True
    assert payload["dry_run"] is True
    assert payload["command"].count("--no-show-model-warnings") >= 1
    assert payload["command"].count("--yes-always") >= 1


def test_nlp_rules_select_client_and_prompt() -> None:
    intent = intent_from_text("aider: napraw testy", default_client="claude")
    assert intent.client_id == "aider"
    assert intent.prompt == "napraw testy"
    assert validate_intent(intent).ok is True


def test_validate_intent_rejects_raw_dsl_without_tillm_drive() -> None:
    intent = ShellIntent(
        client_id="aider",
        prompt="Fix tests",
        raw_dsl={"steps": [{"action": "send_email", "config": {}}]},
    )
    result = validate_intent(intent)
    assert result.ok is False
    assert "raw_dsl has no tillm drive action" in result.errors


def test_intent_contracts_are_exposed_for_ecosystem_validation() -> None:
    assert intent_contracts()
    contracts = validate_intent_contracts()
    assert contracts["ok"] is True
    status = ecosystem_status()
    assert "tillm.drive" in status["expected_actions"]
    assert "intent_contracts" in status
