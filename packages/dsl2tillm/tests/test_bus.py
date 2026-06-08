from dsl2tillm.bus import dispatch


def test_health() -> None:
    result = dispatch("HEALTH")
    assert result.ok is True
    assert result.verb == "HEALTH"


def test_orient() -> None:
    result = dispatch("ORIENT")
    assert result.ok is True
    assert result.verb == "ORIENT"


def test_clients() -> None:
    result = dispatch("CLIENTS")
    assert result.ok is True
    assert "clients" in result.data


def test_actions() -> None:
    result = dispatch("ACTIONS")
    assert result.ok is True
    assert "DRIVE" in result.output


def test_validate_ecosystem() -> None:
    result = dispatch("VALIDATE")
    assert result.verb == "VALIDATE"


def test_resolve() -> None:
    result = dispatch('RESOLVE "aider: fix tests"')
    assert result.ok is True
    assert "DRIVE CLIENT aider" in result.output
