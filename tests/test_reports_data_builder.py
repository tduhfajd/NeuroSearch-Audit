from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db.models import Audit, Base, Issue, Page
from backend.reports.data_builder import build_report_context


def _make_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return session_local()


def test_context_build_is_deterministic() -> None:
    db = _make_session()
    audit = Audit(
        url="https://example.com",
        client_name="Example LLC",
        status="completed",
        seo_score=79.0,
        avri_score=66.0,
        pages_crawled=12,
        created_at=datetime.utcnow(),
    )
    db.add(audit)
    db.flush()

    db.add_all(
        [
            Page(audit_id=audit.id, url="https://example.com/a", inlinks_count=5, word_count=300),
            Page(audit_id=audit.id, url="https://example.com/b", inlinks_count=9, word_count=200),
        ]
    )
    db.add_all(
        [
            Issue(
                audit_id=audit.id,
                rule_id="ANA-01",
                priority="P0",
                title="Noindex",
                description="desc",
                recommendation="fix",
                affected_url="https://example.com/a",
            ),
            Issue(
                audit_id=audit.id,
                rule_id="ANA-03",
                priority="P2",
                title="Meta length",
                description="desc",
                recommendation="fix",
                affected_url="https://example.com/b",
            ),
        ]
    )
    db.commit()

    context_a = build_report_context(db, audit.id).payload
    context_b = build_report_context(db, audit.id).payload

    assert context_a == context_b
    assert context_a["facts"]["issues_total"] == 2
    assert context_a["facts"]["by_priority_count"] == {"P0": 1, "P1": 0, "P2": 1, "P3": 0}
    assert [page["url"] for page in context_a["top_pages"]] == [
        "https://example.com/b",
        "https://example.com/a",
    ]


def test_missing_data_raises_error() -> None:
    db = _make_session()
    audit = Audit(
        url="https://example.com",
        status="completed",
        seo_score=None,
        avri_score=55.0,
        created_at=datetime.utcnow(),
    )
    db.add(audit)
    db.commit()

    with pytest.raises(ValueError, match="seo_score is required"):
        build_report_context(db, audit.id)

