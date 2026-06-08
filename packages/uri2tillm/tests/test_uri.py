from uri2tillm.decode import uri_to_dsl
from uri2tillm.uri import uri_for_client, uri_for_cmd


def test_decode_health_cmd() -> None:
    uri = uri_for_cmd("HEALTH")
    assert uri_to_dsl(uri) == "HEALTH"


def test_decode_drive_client() -> None:
    uri = uri_for_client("aider", prompt="fix tests")
    assert uri_to_dsl(uri) == 'DRIVE CLIENT aider PROMPT "fix tests"'
