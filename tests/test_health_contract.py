from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health_contract_is_stable() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_db_returns_supported_status() -> None:
    response = client.get("/health/db")
    assert response.status_code == 200
    assert response.json().get("status") in {"ok", "degraded"}
