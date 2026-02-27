from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.analyzer.ai_bridge import ReauthRequiredError
from backend.crawler.jobs import run_crawl_job
from backend.db import session as db_session_module
from backend.db.models import Audit, Base, Page
from backend.main import app
from backend.reports.service import ReportServiceError


class _RateLimitedTransport:
    def send_prompt(self, prompt: str) -> str:  # noqa: ARG002
        raise RuntimeError("rate limit")


class _Clock:
    def __init__(self) -> None:
        self.now_value = 0.0
        self.sleeps: list[float] = []

    def now(self) -> float:
        return self.now_value

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now_value += seconds


def _build_session_local() -> sessionmaker:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def _build_client_and_session() -> tuple[TestClient, sessionmaker]:
    session_local = _build_session_local()

    def override_get_db():
        db = session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[db_session_module.get_db] = override_get_db
    return TestClient(app), session_local


def _seed_audit_with_pages(db: Session, *, page_count: int = 1) -> int:
    audit = Audit(
        url="https://example.com",
        status="completed",
        crawl_depth=200,
        pages_crawled=page_count,
        meta={"progress": 100},
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    for idx in range(page_count):
        db.add(
            Page(
                audit_id=audit.id,
                url=f"https://example.com/p/{idx}",
                status_code=200,
                title=f"Title {idx}",
                h1=f"H1 {idx}",
                meta_description="desc",
                canonical=f"https://example.com/p/{idx}",
                robots_meta="index,follow",
                word_count=100,
                inlinks_count=10 - idx,
                crawled_at=datetime.utcnow(),
                ai_scores={"recommendations": "improve block"},
            )
        )
    db.commit()
    return audit.id


def test_error_contract_ai_http_mapping_includes_retryable(monkeypatch: pytest.MonkeyPatch) -> None:
    client, session_local = _build_client_and_session()
    try:
        with session_local() as db:
            audit_id = _seed_audit_with_pages(db)

        monkeypatch.setattr(
            "backend.routers.audits.run_ai_analyze",
            lambda *args, **kwargs: (_ for _ in ()).throw(ReauthRequiredError("session expired")),
        )
        response = client.post(f"/audits/{audit_id}/ai-analyze")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"] == {
        "code": "reauth_required",
        "message": "session expired",
        "retryable": False,
    }


def test_http_mapping_reports_includes_retryable(monkeypatch: pytest.MonkeyPatch) -> None:
    client, session_local = _build_client_and_session()
    try:
        with session_local() as db:
            audit_id = _seed_audit_with_pages(db)

        def _raise_error(*args, **kwargs):
            raise ReportServiceError(
                "persistence_error",
                "Failed to persist generated report",
                retryable=True,
            )

        monkeypatch.setattr("backend.routers.reports.generate_report_artifact", _raise_error)
        response = client.get(f"/audits/{audit_id}/report/pdf")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"] == {
        "code": "persistence_error",
        "message": "Failed to persist generated report",
        "retryable": True,
    }


def test_error_contract_crawler_timeout_recorded(monkeypatch: pytest.MonkeyPatch) -> None:
    session_local = _build_session_local()
    with session_local() as db:
        audit = Audit(
            url="https://example.com",
            status="pending",
            crawl_depth=20,
            pages_crawled=0,
            meta={"progress": 0},
        )
        db.add(audit)
        db.commit()
        db.refresh(audit)

        monkeypatch.setattr(
            "backend.crawler.jobs.execute_crawl_pipeline",
            lambda _: (_ for _ in ()).throw(TimeoutError("crawl deadline exceeded")),
        )

        with pytest.raises(TimeoutError):
            run_crawl_job(audit.id, db)

        refreshed = db.get(Audit, audit.id)

    assert refreshed is not None
    assert refreshed.status == "failed"
    assert refreshed.meta["error"]["code"] == "timeout"
    assert refreshed.meta["error"]["retryable"] is True
    assert refreshed.meta["crawl_errors"][-1]["message"] == "crawl deadline exceeded"
