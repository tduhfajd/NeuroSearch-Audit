from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.analyzer.ai_bridge import ReauthRequiredError, run_ai_analyze
from backend.analyzer.ai_bridge_parser import AIParseError, parse_json_response, parse_with_retries
from backend.analyzer.ai_bridge_prompt import build_page_prompt, prompt_schema_description
from backend.db import session as db_session_module
from backend.db.models import Audit, Base, Page
from backend.main import app


class FakeTransport:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.prompts: list[str] = []
        self._idx = 0

    def send_prompt(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if self._idx >= len(self.responses):
            return self.responses[-1]
        value = self.responses[self._idx]
        self._idx += 1
        return value


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


def _seed_audit_with_pages(db: Session, count: int = 12) -> int:
    audit = Audit(
        url="https://example.com",
        status="completed",
        crawl_depth=200,
        pages_crawled=count,
        meta={"progress": 100},
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    pages = []
    for idx in range(count):
        pages.append(
            Page(
                audit_id=audit.id,
                url=f"https://example.com/p/{idx}",
                status_code=200,
                title=f"Title {idx}",
                h1=f"H1 {idx}",
                meta_description=f"Desc {idx}",
                canonical=f"https://example.com/p/{idx}",
                robots_meta="index,follow",
                word_count=200 + idx,
                inlinks_count=count - idx,
                crawled_at=datetime.utcnow(),
            )
        )
    db.add_all(pages)
    db.commit()
    return audit.id


def test_prompt_schema_contains_required_metric_keys() -> None:
    schema = prompt_schema_description()

    assert "answer_format" in schema
    assert "structure_density" in schema
    assert "definition_coverage" in schema
    assert "authority_signals" in schema
    assert "schema_need" in schema
    assert "recommendations" in schema


def test_prompt_includes_page_snapshot() -> None:
    page = Page(url="https://example.com/page", title="T", h1="H", meta_description="M")

    prompt = build_page_prompt(page)

    assert "Return JSON only" in prompt
    assert "https://example.com/page" in prompt


def test_parser_validation_rejects_out_of_range_metric() -> None:
    with pytest.raises(AIParseError):
        parse_json_response(
            '{"answer_format": 11, "structure_density": 8, "definition_coverage": 8, '
            '"authority_signals": 8, "schema_need": 8, "recommendations": "do x"}'
        )


def test_retry_json_repairs_invalid_first_response() -> None:
    transport = FakeTransport(
        responses=[
            "not-json",
            '{"answer_format": 7, "structure_density": 6, "definition_coverage": 8, '
            '"authority_signals": 6, "schema_need": 5, "recommendations": "Fix FAQ"}',
        ]
    )

    result = parse_with_retries(transport.send_prompt, "initial", max_attempts=3)

    assert result.diagnostics["valid_json"] is True
    assert result.diagnostics["attempts"] == 2
    assert result.parsed["answer_format"] == 7.0


def test_ai_analyze_top10_pages_ai_scores_persisted(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    monkeypatch.setattr("backend.analyzer.ai_bridge.session_health", lambda _: (True, "ok"))

    with session_local() as db:
        audit_id = _seed_audit_with_pages(db, count=12)
        transport = FakeTransport(
            responses=[
                '{"answer_format": 8, "structure_density": 7, "definition_coverage": 6, '
                '"authority_signals": 8, "schema_need": 5, "recommendations": "Add schema"}'
            ]
        )

        summary = run_ai_analyze(db, audit_id, transport=transport)

        pages = (
            db.query(Page)
            .filter(Page.audit_id == audit_id)
            .order_by(Page.inlinks_count.desc(), Page.url.asc())
            .all()
        )

    top_ten = pages[:10]
    tail = pages[10:]

    assert summary.processed_pages == 10
    assert len(transport.prompts) == 10
    assert all(page.ai_scores and page.ai_scores["scores"] for page in top_ten)
    assert all(page.ai_scores is None for page in tail)


def test_ai_analyze_pages_ai_scores_parse_error_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    monkeypatch.setattr("backend.analyzer.ai_bridge.session_health", lambda _: (True, "ok"))

    with session_local() as db:
        audit_id = _seed_audit_with_pages(db, count=1)
        transport = FakeTransport(responses=["bad", "still bad", "again bad"])

        summary = run_ai_analyze(db, audit_id, transport=transport)
        page = db.query(Page).filter(Page.audit_id == audit_id).one()

    assert summary.errors == [f"parse_error:{page.url}"]
    assert page.ai_scores["status"] == "parse_error"
    assert page.ai_scores["diagnostics"]["valid_json"] is False


def test_session_expired_raises_reauth_required(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    monkeypatch.setattr("backend.analyzer.ai_bridge.session_health", lambda _: (False, "expired"))

    with session_local() as db:
        audit_id = _seed_audit_with_pages(db, count=1)
        with pytest.raises(ReauthRequiredError):
            run_ai_analyze(db, audit_id, transport=FakeTransport(["{}"]))


def test_reauth_required_endpoint_returns_409(monkeypatch: pytest.MonkeyPatch) -> None:
    client, session_local = _build_client_and_session()
    try:
        with session_local() as db:
            audit_id = _seed_audit_with_pages(db, count=1)

        def fake_run_ai_analyze(*args, **kwargs):
            raise ReauthRequiredError("session expired")

        monkeypatch.setattr("backend.routers.audits.run_ai_analyze", fake_run_ai_analyze)

        response = client.post(f"/audits/{audit_id}/ai-analyze")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "reauth_required"
