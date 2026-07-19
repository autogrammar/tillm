"""Regression tests for the CLI output-rendering helpers.

These lock in the behaviour of the formatting layer extracted into
:mod:`tillm.cli_output` so it can evolve without changing the observed output.
"""

from __future__ import annotations

import json

import pytest

from tillm.cli_output import (
    _format_client_row,
    _format_drive_summary_line,
    _format_matrix_row,
    _output_stats,
    _print,
    _print_summary,
    _summarize_drive_payload,
    _summarize_drive_result,
)


# ---------------------------------------------------------------------------
# _output_stats
# ---------------------------------------------------------------------------


def test_output_stats_empty_returns_char_count_and_blank_preview() -> None:
    assert _output_stats("") == (0, "")
    assert _output_stats("   ") == (3, "")


def test_output_stats_single_line_strips_and_returns_last_line() -> None:
    assert _output_stats("hello") == (5, "hello")
    assert _output_stats("  spaced  ") == (10, "spaced")


def test_output_stats_multiline_uses_last_non_empty_line() -> None:
    # raw length is len("a\nb\n") == 4; preview is the last non-empty line.
    assert _output_stats("a\nb\n") == (4, "b")


def test_output_stats_truncates_long_preview_with_ellipsis() -> None:
    raw = "x" * 300
    chars, preview = _output_stats(raw)
    assert chars == 300
    assert preview.endswith("…")
    # 199 chars + the single ellipsis char == 200.
    assert preview == "x" * 199 + "…"
    assert len(preview) == 200


# ---------------------------------------------------------------------------
# _format_client_row
# ---------------------------------------------------------------------------


def _full_client_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "id": "aider",
        "label": "Aider",
        "ready": True,
        "available": True,
        "aliases": ["ai"],
        "supports_execute": True,
        "supports_dry_run": True,
        "commands": ["/usr/bin/aider"],
        "command_path": "/usr/bin/aider",
        "supported_execute_profiles": ["default", "automation"],
        "transport": "binary",
        "prompt_mode": "message-file",
    }
    row.update(overrides)
    return row


def test_format_client_row_ready_uses_ok_mark_and_all_fields() -> None:
    out = _format_client_row(_full_client_row())
    assert out.startswith("ok aider")
    assert "mode=message-file" in out
    assert "caps=execute,dry-run" in out
    assert "profiles=default,automation" in out
    assert "transport=binary" in out
    assert "cmd=/usr/bin/aider" in out
    assert "aliases=ai" in out


def test_format_client_row_available_only_uses_tilde_mark() -> None:
    out = _format_client_row(_full_client_row(ready=False, available=True))
    assert out.startswith("~ aider")


def test_format_client_row_unavailable_uses_dash_mark() -> None:
    out = _format_client_row(_full_client_row(ready=False, available=False))
    assert out.startswith("-- aider")


def test_format_client_row_falls_back_to_first_command_when_path_missing() -> None:
    row = _full_client_row(command_path=None)
    out = _format_client_row(row)
    assert "cmd=/usr/bin/aider" in out


def test_format_client_row_unknown_command_when_no_commands() -> None:
    row = _full_client_row(command_path=None, commands=[])
    out = _format_client_row(row)
    assert "cmd=?" in out


def test_format_client_row_renders_empty_caps_profiles_aliases_as_dash() -> None:
    row = _full_client_row(
        supports_execute=False,
        supports_dry_run=False,
        supported_execute_profiles=None,
        aliases=[],
    )
    out = _format_client_row(row)
    assert "caps=-" in out
    assert "profiles=default" in out
    assert "aliases=-" in out


# ---------------------------------------------------------------------------
# _format_matrix_row
# ---------------------------------------------------------------------------


def test_format_matrix_row_ok_result() -> None:
    out = _format_matrix_row(
        {"ok": True, "client_id": "aider", "exit_code": 0, "dry_run": True, "message": "done"}
    )
    assert out.startswith("ok  ")
    assert "aider" in out
    assert "exit=0" in out
    assert "dry_run=True" in out
    assert "done" in out


def test_format_matrix_row_missing_exit_code_shows_dash() -> None:
    out = _format_matrix_row(
        {"ok": False, "client_id": "codex", "exit_code": None, "dry_run": False, "message": "boom"}
    )
    assert "exit=-" in out
    assert "dry_run=False" in out


def test_format_matrix_row_truncates_long_message() -> None:
    out = _format_matrix_row(
        {"ok": True, "client_id": "aider", "exit_code": 0, "dry_run": True, "message": "x" * 60}
    )
    assert "..." in out
    assert "x" * 60 not in out


# ---------------------------------------------------------------------------
# _summarize_drive_result / _summarize_drive_payload
# ---------------------------------------------------------------------------


def test_summarize_drive_result_projects_known_keys_and_drops_unknown() -> None:
    row = {
        "ok": True,
        "client_id": "aider",
        "exit_code": 0,
        "executed": True,
        "dry_run": False,
        "stdout": "applied\n",
        "stderr": "",
        "command": ("aider", "--message-file", "p.md"),
        "extra_junk": "dropped",
        "also_unknown": 42,
    }
    summary = _summarize_drive_result(row)
    assert summary["ok"] is True
    assert summary["client_id"] == "aider"
    assert summary["command"] == ("aider", "--message-file", "p.md")
    assert "extra_junk" not in summary
    assert "also_unknown" not in summary
    assert summary["stdout_chars"] == len("applied\n")
    assert summary["stdout_preview"] == "applied"
    # stderr is empty -> no stderr keys emitted.
    assert "stderr_chars" not in summary


def test_summarize_drive_result_omits_stdout_keys_when_empty() -> None:
    summary = _summarize_drive_result({"ok": True, "client_id": "aider"})
    assert "stdout_chars" not in summary
    assert "stdout_preview" not in summary


def test_summarize_drive_payload_summarizes_results_list() -> None:
    payload = {
        "ok": True,
        "succeeded": 1,
        "failed": 0,
        "results": [{"ok": True, "client_id": "aider", "stdout": "done\n", "verbose": "x" * 400}],
    }
    summarized = _summarize_drive_payload(payload)
    results = summarized["results"]
    assert isinstance(results, list)
    only = results[0]
    assert isinstance(only, dict)
    assert only["client_id"] == "aider"
    assert "verbose" not in only
    assert only["stdout_chars"] == len("done\n")


def test_summarize_drive_payload_summarizes_single_result_key() -> None:
    payload = {"ok": True, "result": {"ok": True, "client_id": "aider", "stdout": "ok\n"}}
    summarized = _summarize_drive_payload(payload)
    result = summarized["result"]
    assert isinstance(result, dict)
    assert result["client_id"] == "aider"
    assert result["stdout_chars"] == len("ok\n")


def test_summarize_drive_payload_treats_bare_client_payload_as_single_result() -> None:
    payload = {"ok": True, "client_id": "aider", "stdout": "done\n"}
    summarized = _summarize_drive_payload(payload)
    assert summarized["stdout_chars"] == len("done\n")


def test_summarize_drive_payload_passthrough_for_unknown_shape() -> None:
    payload: dict[str, object] = {"random": "shape"}
    assert _summarize_drive_payload(payload) == payload


# ---------------------------------------------------------------------------
# _format_drive_summary_line
# ---------------------------------------------------------------------------


def test_format_drive_summary_line_includes_all_extras() -> None:
    line = _format_drive_summary_line(
        {
            "ok": False,
            "client_id": "codex",
            "exit_code": 2,
            "message": "failed",
            "stdout_chars": 100,
            "stdout_preview": "applied edit",
            "stderr_preview": "boom",
            "prompt_path": "/tmp/p.md",
            "error": "TimeoutError",
        }
    )
    assert line.startswith("fail")
    assert "codex" in line
    assert "exit=2" in line
    assert "stdout_chars=100" in line
    assert "stdout_preview='applied edit'" in line
    assert "stderr_preview='boom'" in line
    assert "prompt_path=/tmp/p.md" in line
    assert "error=TimeoutError" in line


def test_format_drive_summary_line_omits_missing_extras() -> None:
    line = _format_drive_summary_line(
        {"ok": True, "client_id": "aider", "exit_code": 0, "message": "done"}
    )
    assert "stdout_chars" not in line
    assert "error" not in line


# ---------------------------------------------------------------------------
# _print / _print_summary (output via stdout)
# ---------------------------------------------------------------------------


def test_print_json_emits_valid_json(capsys: pytest.CaptureFixture[str]) -> None:
    _print({"ok": True, "client_id": "aider"}, "json")
    parsed = json.loads(capsys.readouterr().out)
    assert parsed == {"ok": True, "client_id": "aider"}


def test_print_text_list_emits_client_rows(capsys: pytest.CaptureFixture[str]) -> None:
    _print([_full_client_row(id="aider")], "text")
    out = capsys.readouterr().out
    assert "aider" in out


def test_print_clients_dict_counts_rows_and_lists_errors(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _print(
        {"clients": {"count": 1, "rows": [_full_client_row()], "errors": ["bad config"]}},
        "text",
    )
    out = capsys.readouterr().out
    assert "registered: 1" in out
    assert "aider" in out
    assert "issues:" in out
    assert "bad config" in out


def test_print_summary_list_emits_client_rows(capsys: pytest.CaptureFixture[str]) -> None:
    _print_summary([_full_client_row()])
    out = capsys.readouterr().out
    assert "aider" in out


def test_print_summary_matrix_emits_matrix_header_and_rows(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _print_summary(
        {
            "ok": True,
            "succeeded": 1,
            "failed": 0,
            "message": "ran",
            "results": [{"ok": True, "client_id": "aider", "exit_code": 0, "message": "done"}],
        }
    )
    out = capsys.readouterr().out
    assert "matrix ok=True succeeded=1 failed=0" in out
    assert "aider" in out


def test_print_summary_single_result_emits_line(capsys: pytest.CaptureFixture[str]) -> None:
    _print_summary(
        {"result": {"ok": True, "client_id": "aider", "exit_code": 0, "message": "done"}}
    )
    out = capsys.readouterr().out
    assert "aider" in out
    assert "exit=0" in out
