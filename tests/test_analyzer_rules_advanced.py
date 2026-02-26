from __future__ import annotations

from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.analyzer.service import execute_analysis
from backend.db.models import Audit, Base, Page


def make_db_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return SessionLocal()


def _seed_advanced_dataset(db: Session) -> tuple[Audit, list[Page]]:
    audit = Audit(
        url="https://example.com",
        status="completed",
        crawl_depth=100,
        pages_crawled=3,
        meta={
            "crawl_errors": [{"url": "https://example.com/broken", "error": "HTTP 500"}],
            "redirect_chains": {"https://example.com/old": 3},
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    pages = [
        Page(
            audit_id=audit.id,
            url="https://example.com/ok",
            status_code=200,
            title="Valid Title Length 1234567890123",
            h1="H1",
            meta_description="x" * 130,
            canonical="https://example.com/ok",
            robots_meta="index,follow",
            json_ld=[{"@type": "Organization", "name": "Acme"}],
            word_count=100,
            inlinks_count=1,
            crawled_at=datetime.utcnow(),
        ),
        Page(
            audit_id=audit.id,
            url="https://example.com/404-page",
            status_code=404,
            title="Another title length sample 123456",
            h1="H2",
            meta_description="x" * 130,
            canonical="https://example.com/404-page",
            robots_meta="index,follow",
            json_ld=[{"@type": "Article"}],
            word_count=90,
            inlinks_count=1,
            crawled_at=datetime.utcnow(),
        ),
    ]
    db.add_all(pages)
    db.commit()
    for page in pages:
        db.refresh(page)
    return audit, pages


def test_ana05_detects_broken_pages_crawl_errors_and_redirect_chain() -> None:
    db = make_db_session()
    try:
        audit, pages = _seed_advanced_dataset(db)
        result = execute_analysis(audit=audit, pages=pages)
    finally:
        db.close()

    ana05 = [item for item in result.issue_candidates if item.rule_id == "ANA-05"]
    urls = {item.affected_url for item in ana05}

    assert "https://example.com/404-page" in urls
    assert "https://example.com/broken" in urls
    assert "https://example.com/old" in urls


def test_ana06_flags_missing_required_schema_types() -> None:
    db = make_db_session()
    try:
        audit, pages = _seed_advanced_dataset(db)
        result = execute_analysis(audit=audit, pages=pages)
    finally:
        db.close()

    ana06 = [item for item in result.issue_candidates if item.rule_id == "ANA-06"]
    descriptions = {item.description for item in ana06}

    assert any("FAQPage" in text for text in descriptions)
    assert any("HowTo" in text for text in descriptions)
    assert any("BreadcrumbList" in text for text in descriptions)


def test_ana07_flags_missing_required_schema_fields() -> None:
    db = make_db_session()
    try:
        audit, pages = _seed_advanced_dataset(db)
        result = execute_analysis(audit=audit, pages=pages)
    finally:
        db.close()

    ana07 = [item for item in result.issue_candidates if item.rule_id == "ANA-07"]
    assert any(item.affected_url == "https://example.com/ok" for item in ana07)
    assert any(item.affected_url == "https://example.com/404-page" for item in ana07)
    assert any("Organization" in item.description for item in ana07)
    assert any("Article" in item.description for item in ana07)
