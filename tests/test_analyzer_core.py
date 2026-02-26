from __future__ import annotations

from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.analyzer.rules import IssueCandidate, get_rule_registry
from backend.analyzer.service import execute_analysis
from backend.db.models import Audit, Base, Page


def make_db_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return SessionLocal()


def _seed_minimal_audit_page(db: Session) -> tuple[Audit, list[Page]]:
    audit = Audit(
        url="https://example.com",
        status="completed",
        crawl_depth=50,
        pages_crawled=1,
        meta={"robots_disallow_patterns": ["/private"]},
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    page = Page(
        audit_id=audit.id,
        url="https://example.com/private",
        status_code=200,
        title="Short",
        h1="Heading",
        meta_description="Too short",
        canonical="",
        robots_meta="index,follow",
        json_ld=[],
        word_count=120,
        inlinks_count=1,
        crawled_at=datetime.utcnow(),
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    return audit, [page]


def test_registry_contains_phase3_core_rules() -> None:
    rules = get_rule_registry()
    rule_ids = {rule.rule_id for rule in rules}

    assert {"ANA-01", "ANA-02", "ANA-03", "ANA-04"}.issubset(rule_ids)


def test_issue_contract_and_priority_resolution() -> None:
    issue = IssueCandidate(
        rule_id="ANA-03",
        title="Bad title length",
        description="title too short",
        recommendation="extend title",
        affected_url="https://example.com/private",
        page_id=1,
    )

    assert issue.resolve_priority() == "P2"
    assert issue.rule_id == "ANA-03"
    assert issue.affected_url == "https://example.com/private"
    assert issue.page_id == 1


def test_execute_analysis_returns_issue_candidates_for_registered_rules() -> None:
    db = make_db_session()
    try:
        audit, pages = _seed_minimal_audit_page(db)
        result = execute_analysis(audit=audit, pages=pages)
    finally:
        db.close()

    assert len(result.issue_candidates) >= 2
    assert all(item.rule_id.startswith("ANA-") for item in result.issue_candidates)
    assert all(item.resolve_priority() in {"P0", "P1", "P2", "P3"} for item in result.issue_candidates)


def _seed_pages_for_ana_01_04(db: Session) -> tuple[Audit, list[Page]]:
    audit = Audit(
        url="https://example.com",
        status="completed",
        crawl_depth=100,
        pages_crawled=6,
        meta={"robots_disallow_patterns": ["/blocked"]},
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    pages = [
        Page(
            audit_id=audit.id,
            url="https://example.com/noindex",
            status_code=200,
            title="Duplicate Title",
            h1="Duplicate H1",
            meta_description="x" * 80,
            canonical="https://example.com/noindex",
            robots_meta="noindex,nofollow",
            json_ld=[],
            word_count=200,
            inlinks_count=3,
            crawled_at=datetime.utcnow(),
        ),
        Page(
            audit_id=audit.id,
            url="https://example.com/blocked/landing",
            status_code=200,
            title="Duplicate Title",
            h1="Duplicate H1",
            meta_description="x" * 130,
            canonical="",
            robots_meta="index,follow",
            json_ld=[],
            word_count=160,
            inlinks_count=2,
            crawled_at=datetime.utcnow(),
        ),
        Page(
            audit_id=audit.id,
            url="https://example.com/ok",
            status_code=200,
            title="A" * 65,
            h1="Unique H1",
            meta_description="x" * 130,
            canonical="https://other.com/ok",
            robots_meta="index,follow",
            json_ld=[],
            word_count=180,
            inlinks_count=1,
            crawled_at=datetime.utcnow(),
        ),
        Page(
            audit_id=audit.id,
            url="https://example.com/privacy-policy",
            status_code=200,
            title="Privacy Page",
            h1="Privacy",
            meta_description="x" * 140,
            canonical="https://example.com/privacy-policy",
            robots_meta="noindex,follow",
            json_ld=[],
            word_count=120,
            inlinks_count=1,
            crawled_at=datetime.utcnow(),
        ),
    ]
    db.add_all(pages)
    db.commit()
    for page in pages:
        db.refresh(page)
    return audit, pages


def test_ana01_detects_noindex_and_disallow_but_skips_utility_urls() -> None:
    db = make_db_session()
    try:
        audit, pages = _seed_pages_for_ana_01_04(db)
        result = execute_analysis(audit=audit, pages=pages)
    finally:
        db.close()

    ana01_urls = {item.affected_url for item in result.issue_candidates if item.rule_id == "ANA-01"}
    assert "https://example.com/noindex" in ana01_urls
    assert "https://example.com/blocked/landing" in ana01_urls
    assert "https://example.com/privacy-policy" not in ana01_urls


def test_ana02_detects_duplicate_title_and_h1() -> None:
    db = make_db_session()
    try:
        audit, pages = _seed_pages_for_ana_01_04(db)
        result = execute_analysis(audit=audit, pages=pages)
    finally:
        db.close()

    ana02 = [item for item in result.issue_candidates if item.rule_id == "ANA-02"]
    assert len(ana02) >= 4
    assert any("title" in item.title.lower() for item in ana02)
    assert any("h1" in item.title.lower() for item in ana02)


def test_ana03_checks_title_and_meta_description_lengths() -> None:
    db = make_db_session()
    try:
        audit, pages = _seed_pages_for_ana_01_04(db)
        result = execute_analysis(audit=audit, pages=pages)
    finally:
        db.close()

    ana03 = [item for item in result.issue_candidates if item.rule_id == "ANA-03"]
    assert any(item.affected_url == "https://example.com/noindex" for item in ana03)
    assert any(item.affected_url == "https://example.com/ok" for item in ana03)


def test_ana04_flags_missing_and_cross_domain_canonical() -> None:
    db = make_db_session()
    try:
        audit, pages = _seed_pages_for_ana_01_04(db)
        result = execute_analysis(audit=audit, pages=pages)
    finally:
        db.close()

    ana04_urls = {item.affected_url for item in result.issue_candidates if item.rule_id == "ANA-04"}
    assert "https://example.com/blocked/landing" in ana04_urls
    assert "https://example.com/ok" in ana04_urls
