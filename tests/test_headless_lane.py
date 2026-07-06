"""The headless-cli lane covers every batch-capable client, not just claude — this is the
routing test Koru should use to pick headless over GUI drive."""
from tillm.headless import headless_client_ids, supports_headless


def test_headless_covers_all_execute_capable_clients():
    ids = set(headless_client_ids())
    assert {"claude-code", "codex", "gemini-cli", "qwen-code", "opencode", "devin", "aider"} <= ids


def test_interactive_clients_are_not_headless():
    assert not supports_headless("cline")        # interactive by nature
    assert not supports_headless("qoder")        # GUI IDE, not in registry → GUI/plugin lane
    assert not supports_headless("cursor")


def test_claude_and_aliases_are_headless():
    for alias in ("claude", "claude-code", "anthropic"):
        assert supports_headless(alias)
