from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.analyzer.rules import IssueCandidate
from backend.analyzer.scoring import calculate_seo_score
from backend.analyzer.service import analyze_audit
from backend.db import session as db_session_module
from backend.db.models import Audit, Base, Issue, Page
from backend.main import app


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


def _seed_audit_data(session_local: sessionmaker) -> int:
    with session_local() as db:
        audit = Audit(
            url="https://example.com",
            status="completed",
            crawl_depth=100,
            pages_crawled=2,
            meta={"robots_disallow_patterns": ["/private"]},
        )
        db.add(audit)
        db.commit()
        db.refresh(audit)

        pages = [
            Page(
                audit_id=audit.id,
                url="https://example.com/private",
                status_code=200,
                title="S",
                h1="Same",
                meta_description="short",
                canonical="",
                robots_meta="noindex,nofollow",
                json_ld=[{"@type": "Organization", "name": "Acme"}],
                word_count=120,
                inlinks_count=2,
                crawled_at=datetime.utcnow(),
            ),
            Page(
                audit_id=audit.id,
                url="https://example.com/page",
                status_code=200,
                title="S",
                h1="Same",
                meta_description="x" * 200,
                canonical="https://other.com/page",
                robots_meta="index,follow",
                json_ld=[{"@type": "Article"}],
                word_count=120,
                inlinks_count=2,
                crawled_at=datetime.utcnow(),
            ),
        ]
        db.add_all(pages)
        db.commit()
        return audit.id


def test_score_calculation_clamps_to_0_100_range() -> None:
    many_issues = [
        IssueCandidate(
            rule_id="ANA-01",
            title="t",
            description="d",
            recommendation="r",
            affected_url="https://example.com",
        )
        for _ in range(25)
    ]
    score = calculate_seo_score(many_issues)
    assert 0.0 <= score <= 100.0


def test_scr01_analyze_persists_seo_score_to_audit() -> None:
    client, session_local = _build_client_and_session()
    try:
        audit_id = _seed_audit_data(session_local)
        response = client.post(f"/audits/{audit_id}/analyze")
        body = response.json()

        with session_local() as db:
            audit = db.get(Audit, audit_id)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert body["seo_score"] == audit.seo_score
    assert 0.0 <= audit.seo_score <= 100.0


def test_scr01_analyze_audit_returns_issues_and_score() -> None:
    _, session_local = _build_client_and_session()
    try:
        audit_id = _seed_audit_data(session_local)
        with session_local() as db:
            summary = analyze_audit(db, audit_id)
            issue_rows = db.execute(
                select(func.count()).select_from(Issue).where(Issue.audit_id == audit_id)
            ).scalar_one()
    finally:
        app.dependency_overrides.clear()

    assert summary.issues_created == issue_rows
    assert 0.0 <= summary.seo_score <= 100.0


def test_scr03_issues_endpoint_returns_grouped_priorities() -> None:
    client, session_local = _build_client_and_session()
    try:
        audit_id = _seed_audit_data(session_local)
        analyze_response = client.post(f"/audits/{audit_id}/analyze")
        grouped_response = client.get(f"/audits/{audit_id}/issues")
        grouped = grouped_response.json()
    finally:
        app.dependency_overrides.clear()

    assert analyze_response.status_code == 200
    assert grouped_response.status_code == 200
    assert set(grouped.keys()) == {"P0", "P1", "P2", "P3"}
    assert isinstance(grouped["P0"], list)
    assert isinstance(grouped["P1"], list)
    assert isinstance(grouped["P2"], list)
    assert isinstance(grouped["P3"], list)
    total = len(grouped["P0"]) + len(grouped["P1"]) + len(grouped["P2"]) + len(grouped["P3"])
    assert total == analyze_response.json()["issues_created"]


def test_scr03_issues_endpoint_returns_404_for_missing_audit() -> None:
    client, _ = _build_client_and_session()
    try:
        response = client.get("/audits/999/issues")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
