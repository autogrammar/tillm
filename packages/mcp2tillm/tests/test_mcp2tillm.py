def test_create_server() -> None:
    from mcp2tillm.server import create_server

    server = create_server()
    assert server.name == "tillm"
