from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_returns_ok_status() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_db_returns_known_status() -> None:
    response = client.get("/health/db")
    assert response.status_code == 200
    assert response.json()["status"] in {"ok", "degraded"}


def test_audits_post_validates_payload() -> None:
    response = client.post(
        "/audits",
        json={
            "url": "https://example.com",
            "goal": "wrong",
            "crawl_depth": 200,
        },
    )
    assert response.status_code == 422


def test_audits_get_returns_empty_list() -> None:
    response = client.get("/audits")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
