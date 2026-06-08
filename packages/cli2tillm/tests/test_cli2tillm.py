from dsl2tillm.bus import dispatch


def test_exec_health_via_bus() -> None:
    result = dispatch("HEALTH")
    assert result.ok
