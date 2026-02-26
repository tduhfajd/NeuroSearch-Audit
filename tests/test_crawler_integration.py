from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.crawler.jobs import INMEMORY_QUEUE, run_crawl_job
from backend.crawler.persistence import upsert_pages
from backend.db.models import Audit, Base, Page


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_enqueue_queue_progress_lifecycle(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    audit = Audit(
        url="https://example.com",
        status="pending",
        crawl_depth=20,
        pages_crawled=0,
        meta={"progress": 0},
    )
    db_session.add(audit)
    db_session.commit()
    db_session.refresh(audit)

    monkeypatch.setattr(
        "backend.crawler.jobs.execute_crawl_pipeline",
        lambda _: {
            "pages": [],
            "crawl_errors": [],
            "timed_out": False,
            "robots_status": "ok",
            "sitemap_status": "ok",
            "pagespeed_source": {},
        },
    )

    INMEMORY_QUEUE.jobs.clear()
    INMEMORY_QUEUE.enqueue(run_crawl_job, audit.id, db_session)
    INMEMORY_QUEUE.drain()

    refreshed = db_session.get(Audit, audit.id)
    assert refreshed is not None
    assert refreshed.status == "completed"
    assert refreshed.meta["progress"] == 100


def test_persistence_upsert_updates_existing_row(db_session: Session) -> None:
    audit = Audit(
        url="https://example.com",
        status="crawling",
        crawl_depth=20,
        pages_crawled=0,
        meta={},
    )
    db_session.add(audit)
    db_session.commit()
    db_session.refresh(audit)

    upsert_pages(
        db_session,
        audit_id=audit.id,
        page_payloads=[
            {
                "url": "https://example.com/a",
                "status_code": 200,
                "title": "v1",
                "word_count": 10,
                "json_ld": [],
                "inlinks_count": 0,
                "crawled_at": datetime.utcnow(),
            }
        ],
    )
    db_session.commit()

    upsert_pages(
        db_session,
        audit_id=audit.id,
        page_payloads=[
            {
                "url": "https://example.com/a",
                "status_code": 200,
                "title": "v2",
                "word_count": 42,
                "json_ld": [{"@type": "Article"}],
                "inlinks_count": 3,
                "pagespeed_score": 88.0,
                "crawled_at": datetime.utcnow(),
            }
        ],
    )
    db_session.commit()

    rows = db_session.query(Page).filter(Page.audit_id == audit.id).all()
    assert len(rows) == 1
    assert rows[0].title == "v2"
    assert rows[0].inlinks_count == 3
    assert rows[0].pagespeed_score == 88.0


def test_meta_and_pagespeed_written_after_job(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    audit = Audit(
        url="https://example.com",
        status="pending",
        crawl_depth=20,
        pages_crawled=0,
        meta={"progress": 0},
    )
    db_session.add(audit)
    db_session.commit()
    db_session.refresh(audit)

    monkeypatch.setattr(
        "backend.crawler.jobs.execute_crawl_pipeline",
        lambda _: {
            "pages": [
                {
                    "url": "https://example.com/a",
                    "status_code": 200,
                    "title": "page",
                    "h1": "h",
                    "meta_description": "d",
                    "canonical": "https://example.com/a",
                    "robots_meta": "index,follow",
                    "json_ld": [],
                    "word_count": 20,
                    "inlinks_count": 5,
                    "pagespeed_score": 75.0,
                    "crawled_at": datetime.utcnow(),
                }
            ],
            "crawl_errors": [{"url": "https://example.com/b", "error": "timeout"}],
            "timed_out": False,
            "robots_status": "ok",
            "sitemap_status": "missing",
            "pagespeed_source": {"https://example.com/a": "lighthouse"},
        },
    )

    run_crawl_job(audit.id, db_session)

    refreshed = db_session.get(Audit, audit.id)
    assert refreshed is not None
    assert refreshed.pages_crawled == 1
    assert refreshed.meta["robots_status"] == "ok"
    assert refreshed.meta["sitemap_status"] == "missing"
    assert refreshed.meta["pagespeed_source"]["https://example.com/a"] == "lighthouse"
    assert refreshed.meta["crawl_errors"][0]["error"] == "timeout"
