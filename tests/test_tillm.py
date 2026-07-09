from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

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
from tillm.controller import (
    ClientNotReadyError,
    MultiShellDriveRequest,
    ShellDriveRequest,
    UnknownProfileError,
    build_drive_plan,
    drive_shell_llm_many,
)
from tillm.nlp import ShellIntent, intent_from_text
from tillm.project_env import bootstrap_project_env, load_env_file
from tillm.registry import (
    ShellClientSpec,
    available_client_ids,
    detect_clients,
    get_client_spec,
    iter_client_specs,
    normalize_client_id,
    registered_client_ids,
    resolve_client_ids,
)
from tillm.validation import (
    ecosystem_status,
    intent_contracts,
    validate_client_readiness,
    validate_intent,
    validate_intent_contracts,
    validate_raw_dsl,
)

EXPECTED_CLIENT_IDS = (
    "claude-code",
    "aider",
    "codex",
    "gemini-cli",
    "cline",
    "qwen-code",
    "opencode",
    "devin",
)

AUTOMATION_EXECUTE_ARGS: dict[str, tuple[str, ...]] = {
    "claude-code": ("-p", "--dangerously-skip-permissions"),
    "codex": ("exec", "--dangerously-bypass-approvals-and-sandbox"),
    "gemini-cli": ("-p", "--yolo"),
    "devin": ("-p", "--permission-mode", "dangerous"),
}

EXPECTED_EXECUTE_ARGS: dict[str, tuple[str, ...]] = {
    "claude-code": ("-p",),
    "aider": (),
    "codex": ("exec",),
    "gemini-cli": ("-p", "--approval-mode", "auto_edit"),
    "cline": (),
    "qwen-code": ("-p", "--approval-mode", "yolo"),
    "opencode": ("run", "--dangerously-skip-permissions"),
    "devin": ("-p",),
}


@pytest.mark.parametrize(
    ("alias", "canonical"),
    [
        ("claude", "claude-code"),
        ("codex-cli", "codex"),
        ("openai-codex", "codex"),
        ("gemini", "gemini-cli"),
        ("qwen", "qwen-code"),
        ("open-code", "opencode"),
        ("devin-cli", "devin"),
    ],
)
def test_registry_normalizes_common_aliases(alias: str, canonical: str) -> None:
    assert normalize_client_id(alias) == canonical
    assert get_client_spec(alias) is not None


def test_registry_lists_all_shell_clients() -> None:
    assert shell_client_ids() == EXPECTED_CLIENT_IDS
    for client_id in EXPECTED_CLIENT_IDS:
        spec = get_client_spec(client_id)
        assert spec is not None
        assert spec.id == client_id
        assert spec.commands
        assert spec.prompt_mode in {"stdin", "message-file", "arg"}


def test_detect_clients_marks_available_from_injected_which() -> None:
    rows = detect_clients(
        which=lambda name: f"/bin/{name}" if name == "aider" else None,
        environ={},
    )
    aider = next(row for row in rows if row["id"] == "aider")
    claude = next(row for row in rows if row["id"] == "claude-code")
    assert aider["available"] is True
    assert aider["ready"] is False
    assert claude["available"] is False


def test_detect_clients_reports_capabilities_and_env() -> None:
    env = {"OPENAI_API_KEY": "test-key"}
    rows = detect_clients(
        which=lambda name: f"/bin/{name}" if name == "codex" else None,
        environ=env,
    )
    codex = next(row for row in rows if row["id"] == "codex")
    assert codex["supports_execute"] is True
    assert codex["supports_dry_run"] is True
    assert codex["ready"] is True
    assert codex["missing_env_vars"] == []


@pytest.mark.parametrize("client_id", EXPECTED_CLIENT_IDS)
def test_build_drive_plan_for_each_registered_client(
    client_id: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = get_client_spec(client_id)
    assert spec is not None
    monkeypatch.setattr(
        "shutil.which",
        lambda name: f"/usr/bin/{name}" if name in spec.commands else None,
    )

    plan = build_drive_plan(
        ShellDriveRequest(
            client_id=client_id,
            prompt=f"drive {client_id}",
            project=tmp_path,
        )
    )

    assert plan.spec.id == client_id
    assert plan.argv[0].startswith("/usr/bin/")
    assert plan.prompt_path.exists()
    if spec.prompt_mode == "stdin":
        assert plan.stdin_text is not None
    elif spec.prompt_mode == "message-file":
        assert spec.prompt_file_flag in plan.argv
        assert plan.stdin_text is None


@pytest.mark.parametrize("client_id", EXPECTED_CLIENT_IDS)
def test_execute_args_match_vendor_headless_flags(client_id: str) -> None:
    spec = get_client_spec(client_id)
    assert spec is not None
    assert spec.execute_args == EXPECTED_EXECUTE_ARGS[client_id]


@pytest.mark.parametrize("client_id", [cid for cid in EXPECTED_CLIENT_IDS if cid != "cline"])
def test_build_drive_plan_includes_execute_args_when_executing(
    client_id: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = get_client_spec(client_id)
    assert spec is not None
    for name in spec.env_vars:
        monkeypatch.setenv(name, "test")
    if spec.env_vars_any:
        monkeypatch.setenv(spec.env_vars_any[0], "test")
    monkeypatch.setattr(
        "shutil.which",
        lambda name: f"/usr/bin/{name}" if name in spec.commands else None,
    )

    dry_plan = build_drive_plan(
        ShellDriveRequest(client_id=client_id, prompt="run", project=tmp_path, dry_run=True)
    )
    for arg in spec.execute_args:
        assert arg not in dry_plan.argv

    exec_plan = build_drive_plan(
        ShellDriveRequest(
            client_id=client_id,
            prompt="run",
            project=tmp_path,
            execute=True,
            dry_run=False,
        )
    )
    for arg in spec.execute_args:
        assert arg in exec_plan.argv


def test_build_drive_plan_rejects_execute_for_cline(tmp_path: Path) -> None:
    with pytest.raises(ClientNotReadyError, match="does not support non-interactive"):
        build_drive_plan(
            ShellDriveRequest(
                client_id="cline",
                prompt="run",
                project=tmp_path,
                execute=True,
                dry_run=False,
            )
        )


def test_build_drive_plan_forces_model_flag(tmp_path: Path) -> None:
    import shutil
    from unittest.mock import patch

    def fake_which(name: str) -> str | None:
        return f"/usr/bin/{name}"

    with patch.object(shutil, "which", fake_which):
        plan = build_drive_plan(
            ShellDriveRequest(
                client_id="claude-code",
                prompt="Fix PLF-1",
                project=tmp_path,
                model="sonnet-5",
            )
        )
        assert "--model" in plan.argv
        assert plan.argv[plan.argv.index("--model") + 1] == "claude-sonnet-5"

        codex_plan = build_drive_plan(
            ShellDriveRequest(
                client_id="codex",
                prompt="Fix PLF-1",
                project=tmp_path,
                model="gpt-5",
            )
        )
        assert "-m" in codex_plan.argv

        with pytest.raises(ClientNotReadyError):
            build_drive_plan(
                ShellDriveRequest(
                    client_id="cline",
                    prompt="Fix PLF-1",
                    project=tmp_path,
                    model="sonnet-5",
                )
            )


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


def test_validate_client_readiness_reports_missing_binary_and_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("shutil.which", lambda _name: None)
    monkeypatch.setattr(ShellClientSpec, "has_auth_file", lambda self: False)
    result = validate_client_readiness("codex", environ={})
    assert result.ok is False
    assert any("binary not in PATH" in error for error in result.errors)
    assert any("missing env vars" in error for error in result.errors)


def test_missing_env_vars_satisfied_by_auth_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = get_client_spec("claude-code")
    assert spec is not None
    monkeypatch.setattr(ShellClientSpec, "has_auth_file", lambda self: True)
    assert spec.missing_env_vars({}) == ()
    monkeypatch.setattr(ShellClientSpec, "has_auth_file", lambda self: False)
    assert spec.missing_env_vars({}) == ("ANTHROPIC_API_KEY",)
    assert spec.missing_env_vars({"ANTHROPIC_API_KEY": "x"}) == ()


def test_validate_client_readiness_rejects_execute_for_interactive_only() -> None:
    result = validate_client_readiness("cline", require_execute=True, environ={"OPENAI_API_KEY": "x"})
    assert result.ok is False
    assert any("does not support non-interactive --execute" in error for error in result.errors)


def test_validate_raw_dsl_rejects_unknown_client() -> None:
    errors = validate_raw_dsl(
        {
            "steps": [
                {
                    "action": "tillm.drive",
                    "config": {"client": "unknown-agent", "prompt": "x"},
                }
            ]
        },
        "unknown-agent",
    )
    assert "raw_dsl unknown client" in errors[0]


def test_compat_exports_koru_agent_rows() -> None:
    import shutil
    from unittest.mock import patch

    def fake_which(name: str) -> str | None:
        return "/usr/bin/claude" if name == "claude" else None

    with patch.object(shutil, "which", fake_which):
        rows = detect_koru_agent_rows()
        claude = next(row for row in rows if row["id"] == "claude-code")
        assert "claude-code" in shell_client_ids()

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
        assert registry["codex-cli"]["detect"]["env"] == ["OPENAI_API_KEY"]

        aliases = agent_backend_aliases()
        profiles = agent_backend_profiles()
        if aliases and "tillm_shell" in aliases and profiles:
            backend_profile_id = aliases["tillm_shell"]
            assert profiles[0]["id"] == backend_profile_id


def test_drive_cli_accepts_space_form_extra_arg_flags(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
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


def test_clients_cli_lists_registered_clients(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["clients"])
    out = capsys.readouterr().out
    assert rc == 0
    for client_id in EXPECTED_CLIENT_IDS:
        assert client_id in out


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


def test_ecosystem_status_includes_client_rows() -> None:
    status = ecosystem_status()
    assert status["clients"]["count"] == len(EXPECTED_CLIENT_IDS)
    assert set(status["clients"]["registered"]) == set(EXPECTED_CLIENT_IDS)
    assert len(status["clients"]["rows"]) == len(EXPECTED_CLIENT_IDS)


@pytest.mark.parametrize("client_id", tuple(AUTOMATION_EXECUTE_ARGS))
def test_automation_profile_uses_permission_bypass_flags(
    client_id: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = get_client_spec(client_id)
    assert spec is not None
    for name in spec.env_vars:
        monkeypatch.setenv(name, "test")
    if spec.env_vars_any:
        monkeypatch.setenv(spec.env_vars_any[0], "test")
    monkeypatch.setattr(
        "shutil.which",
        lambda name: f"/usr/bin/{name}" if name in spec.commands else None,
    )

    plan = build_drive_plan(
        ShellDriveRequest(
            client_id=client_id,
            prompt="automate",
            project=tmp_path,
            execute=True,
            dry_run=False,
            execute_profile="automation",
        )
    )
    assert plan.execute_profile == "automation"
    for arg in AUTOMATION_EXECUTE_ARGS[client_id]:
        assert arg in plan.argv


def test_automation_profile_is_rejected_when_unsupported(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setattr("shutil.which", lambda name: f"/usr/bin/{name}" if name == "aider" else None)

    with pytest.raises(UnknownProfileError, match="unsupported execute profile"):
        build_drive_plan(
            ShellDriveRequest(
                client_id="aider",
                prompt="automate",
                project=tmp_path,
                execute=True,
                dry_run=False,
                execute_profile="automation",
            )
        )


def test_drive_cli_accepts_automation_profile(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import subprocess

    class _Proc:
        returncode = 0
        stdout = "ok"
        stderr = ""

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setattr(
        "shutil.which",
        lambda name: f"/usr/bin/{name}" if name == "claude" else None,
    )
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: _Proc())

    rc = main(
        [
            "drive",
            "--client",
            "claude-code",
            "--project",
            str(tmp_path),
            "--prompt",
            "automate",
            "--execute",
            "--profile",
            "automation",
            "--format",
            "json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["execute_profile"] == "automation"
    assert "--dangerously-skip-permissions" in payload["command"]


def test_resolve_client_ids_for_all_available_only(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_available = ("aider", "codex")
    monkeypatch.setattr(
        "tillm.registry.available_client_ids",
        lambda **kwargs: fake_available,
    )
    assert resolve_client_ids(all_clients=True, available_only=True) == fake_available


def test_resolve_client_ids_for_clients_list() -> None:
    assert resolve_client_ids(clients="claude,codex-cli", available_only=False) == (
        "claude-code",
        "codex",
    )


def test_drive_many_plans_all_selected_clients(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "shutil.which",
        lambda name: f"/usr/bin/{name}" if name in {"aider", "codex"} else None,
    )

    matrix = drive_shell_llm_many(
        MultiShellDriveRequest(
            client_ids=("aider", "codex"),
            prompt="review module",
            project=tmp_path,
            dry_run=True,
            parallel=2,
        )
    )

    assert matrix.ok is True
    assert matrix.succeeded == 2
    assert matrix.failed == 0
    assert {result.client_id for result in matrix.results} == {"aider", "codex"}
    assert all(result.dry_run for result in matrix.results)


def test_drive_many_fail_fast_stops_after_first_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "shutil.which",
        lambda name: f"/usr/bin/{name}" if name == "aider" else None,
    )

    matrix = drive_shell_llm_many(
        MultiShellDriveRequest(
            client_ids=("aider", "codex", "claude-code"),
            prompt="review module",
            project=tmp_path,
            dry_run=True,
            parallel=3,
            fail_fast=True,
        )
    )

    assert matrix.ok is False
    assert matrix.failed >= 1
    assert len(matrix.results) <= 3


def test_drive_cli_all_available_clients(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        "tillm.registry.available_client_ids",
        lambda **kwargs: ("aider", "codex"),
    )
    monkeypatch.setattr(
        "shutil.which",
        lambda name: f"/usr/bin/{name}" if name in {"aider", "codex"} else None,
    )

    rc = main(
        [
            "drive",
            "--all",
            "--project",
            str(tmp_path),
            "--prompt",
            "matrix test",
            "--format",
            "json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["ok"] is True
    assert payload["succeeded"] == 2
    assert len(payload["results"]) == 2


def test_registry_lists_transport_metadata() -> None:
    spec = get_client_spec("codex")
    assert spec is not None
    assert spec.transport == "binary"
    assert spec.docker_service == ""
    row = spec.to_dict()
    assert row["docker_service"] == "tillm-codex"


def test_registered_and_available_client_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("shutil.which", lambda name: "/bin/aider" if name == "aider" else None)
    assert len(registered_client_ids()) == len(EXPECTED_CLIENT_IDS)
    assert "aider" in available_client_ids()
    assert "codex" not in available_client_ids()


def test_intent_contracts_are_exposed_for_ecosystem_validation() -> None:
    assert intent_contracts()
    contracts = validate_intent_contracts()
    assert contracts["ok"] is True
    status = ecosystem_status()
    assert "tillm.drive" in status["expected_actions"]
    assert "intent_contracts" in status
    assert "clients" in status


def test_load_env_file_parses_key_value(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        'OPENROUTER_API_KEY=sk-or-test\nLLM_MODEL=openrouter/deepseek/deepseek-v4-pro\n',
        encoding="utf-8",
    )
    values = load_env_file(env_path)
    assert values["OPENROUTER_API_KEY"] == "sk-or-test"
    assert values["LLM_MODEL"] == "openrouter/deepseek/deepseek-v4-pro"


def test_bootstrap_project_env_openrouter_enables_aider(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("AIDER_MODEL", raising=False)
    monkeypatch.setenv("TILLM_ENV2LLM", "0")
    (tmp_path / ".env").write_text(
        "OPENROUTER_API_KEY=sk-or-test\nLLM_MODEL=openrouter/deepseek/deepseek-v4-pro\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("shutil.which", lambda name: "/bin/aider" if name == "aider" else None)

    bootstrap_project_env(tmp_path)
    readiness = validate_client_readiness("aider", require_execute=True)
    assert readiness.ok is True
    assert os.environ.get("AIDER_MODEL") == "openrouter/deepseek/deepseek-v4-pro"


def test_build_drive_plan_bootstraps_env_for_execute(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("TILLM_ENV2LLM", "0")
    (tmp_path / ".env").write_text("OPENROUTER_API_KEY=sk-or-test\n", encoding="utf-8")
    monkeypatch.setattr("shutil.which", lambda name: "/bin/aider" if name == "aider" else None)

    plan = build_drive_plan(
        ShellDriveRequest(
            client_id="aider",
            prompt="smoke",
            project=tmp_path,
            execute=True,
            dry_run=False,
        )
    )
    assert "aider" in plan.shell_preview() or "/bin/aider" in plan.argv[0]


def test_drive_without_prompt_on_tty_fails_fast(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)

    rc = main(["drive", "--client", "aider", "--execute"])

    payload = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert payload["ok"] is False
    assert payload["error"] == "ValueError"
    assert "missing prompt" in payload["message"]


def test_drive_without_prompt_on_empty_stdin_fails_fast(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    monkeypatch.setattr("tillm.cli._stdin_has_data", lambda: False)

    rc = main(["drive", "--client", "aider", "--execute"])

    payload = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert payload["ok"] is False
    assert "missing prompt" in payload["message"]


def test_drive_summary_format_omits_full_stdout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from pathlib import Path as PathType

    from tillm.controller import ShellDriveResult

    prompt_path = tmp_path / "prompt.md"
    prompt_path.write_text("Fix tests\n", encoding="utf-8")
    huge_stdout = ("x" * 5000) + "\nApplied edit to grammar.py\n"
    fake = ShellDriveResult(
        ok=True,
        client_id="aider",
        command=("/usr/bin/aider", "--message-file", str(prompt_path)),
        prompt_path=PathType(prompt_path),
        executed=True,
        dry_run=False,
        exit_code=0,
        stdout=huge_stdout,
        stderr="",
        message="completed",
    )
    monkeypatch.setattr("tillm.cli.drive_shell_llm", lambda _req: fake)

    rc = main(
        [
            "drive",
            "--client",
            "aider",
            "--project",
            str(tmp_path),
            "--prompt",
            "Fix tests",
            "--execute",
            "--format",
            "summary",
        ]
    )

    out = capsys.readouterr().out
    assert rc == 0
    assert "x" * 100 not in out
    assert "Applied edit to grammar.py" in out
    assert "stdout_chars=" in out
    assert "stdout_preview=" in out


def test_drive_without_prompt_writes_tillm_log(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.chdir(tmp_path)

    rc = main(["drive", "--client", "aider", "--execute", "--project", str(tmp_path)])

    assert rc == 2
    log_root = tmp_path / ".tillm" / "logs"
    assert log_root.is_dir()
    jsonl_files = list(log_root.glob("drive-*.jsonl"))
    assert jsonl_files
    lines = jsonl_files[0].read_text(encoding="utf-8").strip().splitlines()
    event = json.loads(lines[-1])
    assert event["phase"] == "prompt_error"
    assert event["client_id"] == "aider"
    assert event["ok"] is False
    latest = json.loads((log_root / "latest.json").read_text(encoding="utf-8"))
    assert latest["phase"] == "prompt_error"


def test_drive_provider_fallback_on_exhaustion(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from tillm.controller import ShellDriveRequest, ShellDriveResult, drive_shell_llm

    monkeypatch.setenv("TILLM_PROVIDER_ORDER", "z.ai,openrouter")
    monkeypatch.setenv("ZAI_API_KEY", "sk-zai")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or")

    calls: list[str | None] = []

    def fake_once(request: ShellDriveRequest) -> ShellDriveResult:
        provider = request.provider
        calls.append(provider)
        if provider == "z.ai":
            return ShellDriveResult(
                ok=False,
                client_id="aider",
                command=("aider",),
                prompt_path=tmp_path / "p.md",
                executed=True,
                dry_run=False,
                stderr="429 Weekly/Monthly Limit Exhausted",
                message="client command failed",
            )
        return ShellDriveResult(
            ok=True,
            client_id="aider",
            command=("aider",),
            prompt_path=tmp_path / "p.md",
            executed=True,
            dry_run=False,
            message="completed",
        )

    monkeypatch.setattr("tillm.controller._drive_shell_llm_once", fake_once)
    result = drive_shell_llm(
        ShellDriveRequest(
            client_id="aider",
            prompt="ok",
            project=tmp_path,
            execute=True,
        )
    )
    assert calls == ["z.ai", "openrouter"]
    assert result.ok is True
    assert result.provider == "openrouter"
    assert result.provider_attempts == ("z.ai", "openrouter")
