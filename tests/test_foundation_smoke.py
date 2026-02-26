from fastapi.testclient import TestClient

from backend.main import create_app



def test_app_initializes_and_exposes_core_routes() -> None:
    client = TestClient(create_app())

    root_response = client.get("/", follow_redirects=False)
    assert root_response.status_code == 307
    assert root_response.headers["location"] == "/static/index.html"
    assert client.get("/health").status_code == 200
    assert client.get("/audits").status_code == 200


def test_audits_invalid_payload_returns_422() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/audits",
        json={"url": "not-a-url", "crawl_depth": 200},
    )
    assert response.status_code == 422
