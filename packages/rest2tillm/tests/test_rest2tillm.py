from fastapi.testclient import TestClient

from rest2tillm.app import create_app


def test_root_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "rest2tillm"
    assert "/v1/dsl" in body["dsl"]


def test_health_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_post_dsl_health() -> None:
    client = TestClient(create_app())
    response = client.post("/v1/dsl", content="HEALTH")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["verb"] == "HEALTH"
