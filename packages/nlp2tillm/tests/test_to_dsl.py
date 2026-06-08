from nlp2tillm.to_dsl import to_dsl


def test_to_dsl_aider() -> None:
    line = to_dsl("aider: fix tests")
    assert line.startswith("DRIVE CLIENT aider")
    assert "fix tests" in line


def test_to_dsl_codex() -> None:
    line = to_dsl("codex plan refactor")
    assert "DRIVE CLIENT codex" in line
