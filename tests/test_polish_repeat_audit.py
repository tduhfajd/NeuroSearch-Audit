from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.analyzer.rules import IssueCandidate
from backend.analyzer.service import analyze_audit
from backend.crawler.persistence import upsert_pages
from backend.db.models import Audit, Base, Issue, Page, Report
from backend.reports.service import generate_report_artifact


class _FakeSummaryTransport:
    def send_prompt(self, prompt: str) -> str:  # noqa: ARG002
        return "Краткое summary."


class _DuplicateRule:
    rule_id = "ANA-01"

    def evaluate(self, context) -> list[IssueCandidate]:  # noqa: ANN001
        page = context.pages[0]
        issue = IssueCandidate(
            rule_id="ANA-01",
            title="Duplicate issue",
            description="desc",
            recommendation="fix",
            affected_url=page.url,
            page_id=page.id,
        )
        return [issue, issue]


def _build_session_local() -> sessionmaker:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def _create_audit(db: Session, domain_url: str) -> int:
    audit = Audit(
        url=domain_url,
        client_name="ООО Пример",
        status="completed",
        crawl_depth=200,
        pages_crawled=1,
        seo_score=70.0,
        avri_score=60.0,
        meta={"progress": 100},
        created_at=datetime.utcnow(),
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit.id


def _seed_report_inputs(db: Session, audit_id: int) -> None:
    db.add(
        Page(
            audit_id=audit_id,
            url=f"https://example.com/audit-{audit_id}/page",
            status_code=200,
            title="Title",
            h1="H1",
            meta_description="desc",
            canonical=f"https://example.com/audit-{audit_id}/page",
            robots_meta="index,follow",
            word_count=100,
            inlinks_count=10,
            crawled_at=datetime.utcnow(),
            ai_scores={"recommendations": "Сделать блок FAQ и schema.org."},
        )
    )
    db.add(
        Issue(
            audit_id=audit_id,
            rule_id="ANA-01",
            priority="P1",
            title="Issue",
            description="desc",
            recommendation="fix",
            affected_url=f"https://example.com/audit-{audit_id}/page",
        )
    )
    db.commit()


def test_idempotent_upsert_and_repeat_audit_isolation() -> None:
    session_local = _build_session_local()
    with session_local() as db:
        first_audit_id = _create_audit(db, "https://example.com")
        second_audit_id = _create_audit(db, "https://example.com")

        upsert_pages(
            db,
            audit_id=first_audit_id,
            page_payloads=[
                {"url": "https://example.com/about", "title": "v1"},
                {"url": "https://example.com/about", "title": "v2"},
            ],
        )
        db.commit()

        upsert_pages(
            db,
            audit_id=second_audit_id,
            page_payloads=[
                {"url": "https://example.com/about", "title": "v3"},
            ],
        )
        db.commit()

        first_pages = db.query(Page).filter(Page.audit_id == first_audit_id).all()
        second_pages = db.query(Page).filter(Page.audit_id == second_audit_id).all()

    assert len(first_pages) == 1
    assert first_pages[0].title == "v2"
    assert len(second_pages) == 1
    assert second_pages[0].title == "v3"


def test_report_artifact_isolation_distinct_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    session_local = _build_session_local()
    monkeypatch.setattr("backend.reports.service.session_health", lambda: (True, "ok"))

    with session_local() as db:
        first_audit_id = _create_audit(db, "https://example.com")
        second_audit_id = _create_audit(db, "https://example.com")
        _seed_report_inputs(db, first_audit_id)
        _seed_report_inputs(db, second_audit_id)

        first = generate_report_artifact(
            db,
            audit_id=first_audit_id,
            report_type="full_report",
            storage_dir=tmp_path,
            summary_transport_factory=_FakeSummaryTransport,
        )
        second = generate_report_artifact(
            db,
            audit_id=second_audit_id,
            report_type="full_report",
            storage_dir=tmp_path,
            summary_transport_factory=_FakeSummaryTransport,
        )
        rows = db.query(Report).order_by(Report.id.asc()).all()

    assert first.file_path.exists()
    assert second.file_path.exists()
    assert first.file_path != second.file_path
    assert f"audit_{first_audit_id}" in str(first.file_path)
    assert f"audit_{second_audit_id}" in str(second.file_path)
    assert len(rows) == 2
    assert rows[0].file_path != rows[1].file_path


def test_repeat_audit_cycle_generates_isolated_results(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    session_local = _build_session_local()
    monkeypatch.setattr("backend.reports.service.session_health", lambda: (True, "ok"))

    with session_local() as db:
        first_audit_id = _create_audit(db, "https://example.com")
        second_audit_id = _create_audit(db, "https://example.com")
        _seed_report_inputs(db, first_audit_id)
        _seed_report_inputs(db, second_audit_id)

        summary_one = analyze_audit(db, first_audit_id, rules=[_DuplicateRule()])
        summary_two = analyze_audit(db, second_audit_id, rules=[_DuplicateRule()])

        first_report = generate_report_artifact(
            db,
            audit_id=first_audit_id,
            report_type="kp",
            storage_dir=tmp_path,
            summary_transport_factory=_FakeSummaryTransport,
        )
        second_report = generate_report_artifact(
            db,
            audit_id=second_audit_id,
            report_type="kp",
            storage_dir=tmp_path,
            summary_transport_factory=_FakeSummaryTransport,
        )

        first_issues = db.query(Issue).filter(Issue.audit_id == first_audit_id).all()
        second_issues = db.query(Issue).filter(Issue.audit_id == second_audit_id).all()
        reports = db.query(Report).filter(Report.type == "kp").all()
        first_audit_reports = db.query(Report).filter(Report.audit_id == first_audit_id).all()
        second_audit_reports = db.query(Report).filter(Report.audit_id == second_audit_id).all()

    assert summary_one.audit_id == first_audit_id
    assert summary_two.audit_id == second_audit_id
    assert len(first_issues) == 1
    assert len(second_issues) == 1
    assert first_report.file_path != second_report.file_path
    assert len(reports) == 2
    assert len(first_audit_reports) == 1
    assert len(second_audit_reports) == 1
