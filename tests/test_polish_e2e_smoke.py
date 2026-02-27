from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.crawler.jobs import run_crawl_job
from backend.db import session as db_session_module
from backend.db.models import Audit, Base, Page
from backend.main import app


class _AITransport:
    def send_prompt(self, prompt: str) -> str:  # noqa: ARG002
        return (
            "{"
            '"answer_format": 8, '
            '"structure_density": 7, '
            '"definition_coverage": 6, '
            '"authority_signals": 7, '
            '"schema_need": 5, '
            '"recommendations": "Добавить блок FAQ и schema.org"'
            "}"
        )


class _SummaryTransport:
    def send_prompt(self, prompt: str) -> str:  # noqa: ARG002
        return "Приоритет: устранить критичные проблемы и усилить структуру ответа."


def _build_client_and_session() -> tuple[TestClient, sessionmaker]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    def override_get_db():
        db = session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[db_session_module.get_db] = override_get_db
    return TestClient(app), session_local


def _fake_crawl_result(*, js_heavy: bool) -> dict[str, object]:
    return {
        "pages": [
            {
                "url": "https://example.com/page-1",
                "status_code": 200,
                "title": "Page 1",
                "h1": "Heading",
                "meta_description": "Desc",
                "canonical": "https://example.com/page-1",
                "robots_meta": "index,follow",
                "json_ld": [],
                "word_count": 250,
                "inlinks_count": 10,
                "pagespeed_score": 80.0,
                "crawled_at": datetime.utcnow(),
            }
        ],
        "crawl_errors": [],
        "timed_out": js_heavy,
        "spa_diagnostics": {
            "spa_timeout_count": 1 if js_heavy else 0,
            "spa_fallback_count": 1 if js_heavy else 0,
            "spa_retry_count": 1 if js_heavy else 0,
        },
        "robots_status": "ok",
        "sitemap_status": "ok",
        "pagespeed_source": {"https://example.com/page-1": "lighthouse"},
    }


def test_readme_sections_cover_ops_runbook_readme_sections() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "## Prerequisites" in readme
    assert "## Install And Run" in readme
    assert "## First Audit Flow" in readme
    assert "## Known Limits" in readme
    assert "## Troubleshooting" in readme
    assert "## Recovery Steps" in readme
    assert "## Operational Invariants" in readme


def test_readme_runbook_commands_present_runbook_commands() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "python -m backend.analyzer.ai_bridge --setup" in readme
    assert "uvicorn backend.main:app --reload --port 8000" in readme
    assert "POST http://127.0.0.1:8000/audits" in readme
    assert "GET /audits/<AUDIT_ID>/report/pdf" in readme


def test_content_site_full_chain_smoke_generates_pdf(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, session_local = _build_client_and_session()
    try:
        monkeypatch.setattr("backend.routers.audits.enqueue_crawl_job", lambda audit_id: "job-1")
        monkeypatch.setattr(
            "backend.crawler.jobs.execute_crawl_pipeline", lambda audit: _fake_crawl_result(js_heavy=False)
        )
        monkeypatch.setattr("backend.analyzer.ai_bridge.session_health", lambda _: (True, "ok"))
        monkeypatch.setattr("backend.reports.service.session_health", lambda: (True, "ok"))
        monkeypatch.setattr("backend.routers.audits.PlaywrightChatGPTTransport", _AITransport)
        monkeypatch.setattr("backend.reports.service.REPORTS_DIR", tmp_path)
        monkeypatch.setattr("backend.reports.service.DEFAULT_CHATGPT_TRANSPORT_FACTORY", _SummaryTransport)

        create_response = client.post(
            "/audits",
            json={
                "url": "https://example.com",
                "client_name": "ООО Пример",
                "goal": "leads",
                "crawl_depth": 200,
            },
        )
        audit_id = create_response.json()["id"]

        with session_local() as db:
            run_crawl_job(audit_id, db)

        analyze_response = client.post(f"/audits/{audit_id}/analyze")
        ai_response = client.post(f"/audits/{audit_id}/ai-analyze")
        report_response = client.get(f"/audits/{audit_id}/report/pdf")
    finally:
        app.dependency_overrides.clear()

    assert create_response.status_code == 201
    assert analyze_response.status_code == 200
    assert ai_response.status_code == 200
    assert ai_response.json()["status"] in {"ok", "partial"}
    assert report_response.status_code == 200
    assert report_response.content.startswith(b"%PDF")


def test_js_heavy_full_chain_smoke_keeps_non_fatal_behavior_js_heavy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client, session_local = _build_client_and_session()
    try:
        monkeypatch.setattr("backend.routers.audits.enqueue_crawl_job", lambda audit_id: "job-1")
        monkeypatch.setattr(
            "backend.crawler.jobs.execute_crawl_pipeline", lambda audit: _fake_crawl_result(js_heavy=True)
        )
        monkeypatch.setattr("backend.analyzer.ai_bridge.session_health", lambda _: (True, "ok"))
        monkeypatch.setattr("backend.reports.service.session_health", lambda: (True, "ok"))
        monkeypatch.setattr("backend.routers.audits.PlaywrightChatGPTTransport", _AITransport)
        monkeypatch.setattr("backend.reports.service.REPORTS_DIR", tmp_path)
        monkeypatch.setattr("backend.reports.service.DEFAULT_CHATGPT_TRANSPORT_FACTORY", _SummaryTransport)

        create_response = client.post(
            "/audits",
            json={
                "url": "https://example.com",
                "client_name": "ООО Пример",
                "goal": "leads",
                "crawl_depth": 200,
            },
        )
        audit_id = create_response.json()["id"]

        with session_local() as db:
            run_crawl_job(audit_id, db)
            audit = db.get(Audit, audit_id)

        analyze_response = client.post(f"/audits/{audit_id}/analyze")
        ai_response = client.post(f"/audits/{audit_id}/ai-analyze")
        report_response = client.get(f"/audits/{audit_id}/report/pdf")
    finally:
        app.dependency_overrides.clear()

    assert create_response.status_code == 201
    assert analyze_response.status_code == 200
    assert ai_response.status_code == 200
    assert ai_response.json()["status"] in {"ok", "partial"}
    assert report_response.status_code == 200
    assert audit is not None
    assert audit.meta["timed_out"] is True
    assert audit.meta["spa_diagnostics"]["spa_timeout_count"] == 1
