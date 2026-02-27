from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.analyzer.ai_bridge import RateLimitError, ReauthRequiredError, run_ai_analyze
from backend.crawler.jobs import run_crawl_job
from backend.crawler.playwright_utils import render_with_timeout_policy
from backend.db import session as db_session_module
from backend.db.models import Audit, Base, Page
from backend.main import app
from backend.reports.service import ReportServiceError


class _BackoffTransport:
    def __init__(self, *, fail_attempts: int, response: str) -> None:
        self.fail_attempts = fail_attempts
        self.response = response
        self.calls = 0

    def send_prompt(self, prompt: str) -> str:  # noqa: ARG002
        self.calls += 1
        if self.calls <= self.fail_attempts:
            raise RateLimitError("rate limited")
        return self.response


class _SequencedTransport:
    def __init__(self, responses: list[str | Exception]) -> None:
        self.responses = responses
        self.calls = 0

    def send_prompt(self, prompt: str) -> str:  # noqa: ARG002
        item = self.responses[self.calls]
        self.calls += 1
        if isinstance(item, Exception):
            raise item
        return item


class _Clock:
    def __init__(self) -> None:
        self.now_value = 0.0
        self.sleeps: list[float] = []

    def now(self) -> float:
        return self.now_value

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now_value += seconds


class _TimeoutRenderer:
    def __init__(self, fail_attempts: int, html: str = "<html><body>rendered</body></html>") -> None:
        self.fail_attempts = fail_attempts
        self.html = html
        self.calls = 0
        self.timeouts: list[int] = []

    def render(
        self, url: str, timeout_ms: int = 15000, wait_until: str = "domcontentloaded"
    ) -> str:
        _ = (url, wait_until)
        self.calls += 1
        self.timeouts.append(timeout_ms)
        if self.calls <= self.fail_attempts:
            raise TimeoutError("page render timeout")
        return self.html


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


def _valid_ai_json() -> str:
    return (
        "{"
        '"answer_format": 8, '
        '"structure_density": 7, '
        '"definition_coverage": 6, '
        '"authority_signals": 7, '
        '"schema_need": 5, '
        '"recommendations": "Actionable recommendation"'
        "}"
    )


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


def test_spa_timeout_fallback_waits_switches_to_http() -> None:
    renderer = _TimeoutRenderer(fail_attempts=6)
    html = "<html><body><div id='app'></div><script></script></body></html>"

    outcome = render_with_timeout_policy(
        url="https://example.com",
        http_html=html,
        renderer=renderer,
        timeout_steps_ms=(100, 200, 300),
        retry_budget=1,
    )

    assert outcome.timed_out is True
    assert outcome.used_playwright is False
    assert outcome.reason.endswith("timeout_fallback")
    assert outcome.fallback_attempts == 6


def test_retry_budget_limits_render_attempts() -> None:
    renderer = _TimeoutRenderer(fail_attempts=10)
    html = "<html><body><div id='app'></div><script></script></body></html>"

    outcome = render_with_timeout_policy(
        url="https://example.com",
        http_html=html,
        renderer=renderer,
        timeout_steps_ms=(50, 100),
        retry_budget=2,
    )

    assert outcome.used_playwright is False
    assert outcome.fallback_attempts == 6
    assert renderer.calls == 6
    assert renderer.timeouts == [50, 100, 50, 100, 50, 100]


def test_rate_limit_backoff_sequence_is_exponential(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("backend.analyzer.ai_bridge.session_health", lambda _: (True, "ok"))
    session_local = _build_session_local()
    clock = _Clock()

    with session_local() as db:
        audit_id = _seed_audit_with_pages(db, page_count=1)
        transport = _BackoffTransport(fail_attempts=2, response=_valid_ai_json())
        summary = run_ai_analyze(
            db,
            audit_id,
            transport=transport,
            min_interval_seconds=0.0,
            max_rate_limit_retries=2,
            sleep_func=clock.sleep,
            time_func=clock.now,
        )

    assert summary.status == "ok"
    assert summary.errors == []
    assert clock.sleeps == [2.0, 4.0]


def test_non_fatal_rate_limit_continues_next_page(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("backend.analyzer.ai_bridge.session_health", lambda _: (True, "ok"))
    session_local = _build_session_local()

    with session_local() as db:
        audit_id = _seed_audit_with_pages(db, page_count=2)
        transport = _SequencedTransport(
            responses=[
                RateLimitError("rl-1"),
                RateLimitError("rl-2"),
                _valid_ai_json(),
            ]
        )
        summary = run_ai_analyze(
            db,
            audit_id,
            transport=transport,
            min_interval_seconds=0.0,
            max_rate_limit_retries=1,
            sleep_func=lambda _: None,
            time_func=lambda: 0.0,
        )
        pages = (
            db.query(Page)
            .filter(Page.audit_id == audit_id)
            .order_by(Page.inlinks_count.desc(), Page.url.asc())
            .all()
        )

    assert summary.status == "partial"
    assert len(summary.errors) == 1
    assert summary.errors[0].startswith("rate_limit_error:")
    assert pages[0].ai_scores["status"] == "rate_limit_error"
    assert pages[1].ai_scores["scores"]["answer_format"] == 8
