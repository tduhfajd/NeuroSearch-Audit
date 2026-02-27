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

    assert 'x-data="dashboardApp()"' in html
    assert "function dashboardApp()" in html
    assert "syncFromUrl" in html
    assert "setView" in html


def test_audit_list_contains_expected_table_markup() -> None:
    html = _read_index()

    assert "Список аудитов" in html
    assert "loadAudits" in html
    assert "filteredAudits" in html


def test_filters_are_declared_for_operational_statuses() -> None:
    html = _read_index()

    assert "'all', 'in-progress', 'completed', 'failed'" in html
    assert "statusFilter" in html
    assert "statusFilterLabel" in html


def test_columns_match_dashboard_list_contract() -> None:
    html = _read_index()

    assert "Домен" in html
    assert "Дата" in html
    assert "SEO Score" in html
    assert "AVRI" in html
    assert "Статус" in html


def test_create_form_contains_required_inputs() -> None:
    html = _read_index()

    assert "Запуск нового аудита" in html
    assert 'x-model.trim="createForm.url"' in html
    assert 'x-model="createForm.goal"' in html
    assert 'x-model.number="createForm.crawl_depth"' in html


def test_submit_flow_posts_to_audits_endpoint() -> None:
    html = _read_index()

    assert '@submit.prevent="submitCreateAudit()"' in html
    assert 'await fetch("/audits"' in html
    assert 'method: "POST"' in html


def test_progress_redirect_after_successful_submit() -> None:
    html = _read_index()

    assert 'this.setView("progress", createdAudit.id)' in html


def test_progress_polling_uses_status_endpoint_every_2_seconds() -> None:
    html = _read_index()

    assert "startProgressPolling" in html
    assert "fetch(`/audits/${auditId}/status`)" in html
    assert "setInterval(tick, 2000)" in html


def test_status_transition_to_result_after_completion() -> None:
    html = _read_index()

    assert '["completed", "failed"].includes(payload.status)' in html
    assert 'if (payload.status === "completed")' in html
    assert 'this.setView("result", auditId)' in html


def test_interval_cleanup_is_implemented_when_view_changes() -> None:
    html = _read_index()

    assert "stopProgressPolling" in html
    assert "clearInterval(this.progressPollTimer)" in html
    assert 'this.view === "progress" && nextView !== "progress"' in html
