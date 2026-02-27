import time

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_ai_bridge_health_returns_ok(monkeypatch) -> None:
    monkeypatch.setattr("backend.routers.ai_bridge.session_health", lambda: (True, "ok"))

    response = client.get("/ai-bridge/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "detail": "ok"}


def test_ai_bridge_health_returns_reauth_required(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.routers.ai_bridge.session_health",
        lambda: (False, "storage state missing"),
    )

    response = client.get("/ai-bridge/health")

    assert response.status_code == 200
    assert response.json() == {"status": "reauth_required", "detail": "storage state missing"}


def test_ai_bridge_setup_start_and_status_completed(monkeypatch) -> None:
    monkeypatch.setattr("backend.routers.ai_bridge.setup_session_state", lambda: None)

    start_response = client.post("/ai-bridge/setup/start")
    assert start_response.status_code == 200
    assert start_response.json()["status"] in {"running", "completed"}

    for _ in range(20):
        status_response = client.get("/ai-bridge/setup/status")
        payload = status_response.json()
        if payload["status"] == "completed":
            break
        time.sleep(0.01)
    else:
        raise AssertionError("setup did not complete in time")

    assert payload["status"] == "completed"


def test_ai_bridge_setup_status_failed(monkeypatch) -> None:
    from backend.analyzer.ai_bridge_session import SessionStateError

    def _raise() -> None:
        raise SessionStateError("setup failed")

    monkeypatch.setattr("backend.routers.ai_bridge.setup_session_state", _raise)

    start_response = client.post("/ai-bridge/setup/start")
    assert start_response.status_code == 200

    for _ in range(20):
        status_response = client.get("/ai-bridge/setup/status")
        payload = status_response.json()
        if payload["status"] == "failed":
            break
        time.sleep(0.01)
    else:
        raise AssertionError("setup failure did not propagate")

    assert payload["status"] == "failed"
    assert "setup failed" in (payload["detail"] or "")
