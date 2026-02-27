from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app


def _read_index() -> str:
    path = Path("frontend/static/index.html")
    return path.read_text(encoding="utf-8")


def test_layout_root_redirects_to_static_dashboard() -> None:
    client = TestClient(app)

    response = client.get("/", follow_redirects=False)

    assert response.status_code in {307, 308}
    assert response.headers["location"] == "/static/index.html"


def test_layout_static_dashboard_is_served() -> None:
    client = TestClient(app)

    response = client.get("/static/index.html")

    assert response.status_code == 200
    assert "NeuroSearch Dashboard" in response.text


def test_routing_views_are_declared_in_index_markup() -> None:
    html = _read_index()

    assert "view === 'list'" in html
    assert "view === 'create'" in html
    assert "view === 'progress'" in html
    assert "view === 'result'" in html


def test_alpine_is_used_for_state_routing() -> None:
    html = _read_index()

    assert "x-data=\"dashboardApp()\"" in html
    assert "function dashboardApp()" in html
    assert "syncFromUrl" in html
    assert "setView" in html
