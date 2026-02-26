from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.analyzer.ai_bridge import RateLimitError, run_ai_analyze
from backend.analyzer.scoring import calculate_avri_score
from backend.db.models import Audit, Base, Page


class Clock:
    def __init__(self) -> None:
        self._now = 0.0
        self.sleeps: list[float] = []

    def now(self) -> float:
        return self._now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self._now += seconds


class SequencedTransport:
    def __init__(
        self,
        responses: list[str],
        fail_first: int = 0,
        always_rate_limit: bool = False,
    ) -> None:
        self.responses = responses
        self.prompts: list[str] = []
        self._idx = 0
        self._fails_left = fail_first
        self._always_rate_limit = always_rate_limit

    def send_prompt(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if self._always_rate_limit:
            raise RateLimitError("rate limited")
        if self._fails_left > 0:
            self._fails_left -= 1
            raise RateLimitError("rate limited")
        if self._idx >= len(self.responses):
            return self.responses[-1]
        response = self.responses[self._idx]
        self._idx += 1
        return response


def _build_session_local() -> sessionmaker:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def _seed_pages(db: Session, count: int) -> int:
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

    rows = [
        Page(
            audit_id=audit.id,
            url=f"https://example.com/page-{idx}",
            status_code=200,
            title=f"Title {idx}",
            h1=f"H1 {idx}",
            meta_description=f"Desc {idx}",
            canonical=f"https://example.com/page-{idx}",
            robots_meta="index,follow",
            word_count=300,
            inlinks_count=100 - idx,
            crawled_at=datetime.utcnow(),
        )
        for idx in range(count)
    ]
    db.add_all(rows)
    db.commit()
    return audit.id


def _valid_response(
    answer: int,
    structure: int,
    definition: int,
    authority: int,
    schema: int,
) -> str:
    return (
        "{"
        f'"answer_format": {answer}, '
        f'"structure_density": {structure}, '
        f'"definition_coverage": {definition}, '
        f'"authority_signals": {authority}, '
        f'"schema_need": {schema}, '
        '"recommendations": "Actionable recommendation"'
        "}"
    )


def test_pacing_waits_between_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    session_local = _build_session_local()
    clock = Clock()
    monkeypatch.setattr("backend.analyzer.ai_bridge.session_health", lambda _: (True, "ok"))

    with session_local() as db:
        audit_id = _seed_pages(db, count=2)
        transport = SequencedTransport(responses=[_valid_response(8, 7, 6, 7, 5)])

        summary = run_ai_analyze(
            db,
            audit_id,
            transport=transport,
            min_interval_seconds=15.0,
            sleep_func=clock.sleep,
            time_func=clock.now,
        )

    assert summary.processed_pages == 2
    assert len(clock.sleeps) == 1
    assert clock.sleeps[0] == 15.0


def test_rate_limit_backoff_retries_then_success(monkeypatch: pytest.MonkeyPatch) -> None:
    session_local = _build_session_local()
    clock = Clock()
    monkeypatch.setattr("backend.analyzer.ai_bridge.session_health", lambda _: (True, "ok"))

    with session_local() as db:
        audit_id = _seed_pages(db, count=1)
        transport = SequencedTransport(
            responses=[_valid_response(8, 7, 6, 7, 5)],
            fail_first=1,
        )

        summary = run_ai_analyze(
            db,
            audit_id,
            transport=transport,
            min_interval_seconds=0.0,
            max_rate_limit_retries=2,
            sleep_func=clock.sleep,
            time_func=clock.now,
        )

    assert summary.errors == []
    assert clock.sleeps == [2.0]


def test_rate_limit_exhausted_no_crash_marks_page_error(monkeypatch: pytest.MonkeyPatch) -> None:
    session_local = _build_session_local()
    clock = Clock()
    monkeypatch.setattr("backend.analyzer.ai_bridge.session_health", lambda _: (True, "ok"))

    with session_local() as db:
        audit_id = _seed_pages(db, count=1)
        transport = SequencedTransport(responses=["{}"], always_rate_limit=True)

        summary = run_ai_analyze(
            db,
            audit_id,
            transport=transport,
            min_interval_seconds=0.0,
            max_rate_limit_retries=1,
            sleep_func=clock.sleep,
            time_func=clock.now,
        )
        page = db.query(Page).filter(Page.audit_id == audit_id).one()

    assert summary.processed_pages == 1
    assert summary.errors == [f"rate_limit_error:{page.url}"]
    assert page.ai_scores["status"] == "rate_limit_error"
    assert clock.sleeps == [2.0]


def test_avri_scr02_aggregation_persisted(monkeypatch: pytest.MonkeyPatch) -> None:
    session_local = _build_session_local()
    monkeypatch.setattr("backend.analyzer.ai_bridge.session_health", lambda _: (True, "ok"))

    with session_local() as db:
        audit_id = _seed_pages(db, count=2)
        transport = SequencedTransport(
            responses=[
                _valid_response(8, 6, 7, 5, 4),
                _valid_response(6, 8, 9, 7, 6),
            ]
        )

        summary = run_ai_analyze(
            db,
            audit_id,
            transport=transport,
            min_interval_seconds=0.0,
            sleep_func=lambda _: None,
            time_func=lambda: 0.0,
        )
        audit = db.get(Audit, audit_id)

    assert summary.avri_score == 67.0
    assert audit.avri_score == 67.0


def test_avri_aggregation_returns_none_for_empty_rows() -> None:
    assert calculate_avri_score([]) is None
