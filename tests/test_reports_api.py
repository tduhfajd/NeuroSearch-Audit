from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db.models import Audit, Base, Issue, Page, Report
from backend.reports.service import ReportServiceError, generate_report_artifact


def _build_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def _seed_audit_data(session_local) -> int:
    with session_local() as db:
        audit = Audit(
            url="https://example.com",
            client_name="ООО Пример",
            status="completed",
            seo_score=74.0,
            avri_score=61.0,
            pages_crawled=20,
            created_at=datetime.utcnow(),
        )
        db.add(audit)
        db.flush()
        db.add(
            Page(
                audit_id=audit.id,
                url="https://example.com/page",
                inlinks_count=8,
                ai_scores={"recommendations": "Усилить структурные блоки FAQ."},
            )
        )
        db.add(
            Issue(
                audit_id=audit.id,
                rule_id="ANA-01",
                priority="P1",
                title="Noindex",
                description="desc",
                recommendation="fix",
                affected_url="https://example.com/page",
            )
        )
        db.commit()
        return audit.id


def test_service_generates_and_persists_report(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    session_local = _build_session()
    audit_id = _seed_audit_data(session_local)
    monkeypatch.setattr("backend.reports.service.session_health", lambda: (True, "ok"))

    with session_local() as db:
        result = generate_report_artifact(
            db,
            audit_id=audit_id,
            report_type="full_report",
            storage_dir=tmp_path,
        )
        persisted = db.query(Report).filter(Report.audit_id == audit_id).all()

    assert result.file_path.exists()
    assert result.file_path.read_bytes().startswith(b"%PDF")
    assert len(persisted) == 1
    assert persisted[0].type == "full_report"


def test_ai_text_strict_mode_requires_session(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    session_local = _build_session()
    audit_id = _seed_audit_data(session_local)
    monkeypatch.setattr(
        "backend.reports.service.session_health",
        lambda: (False, "storage state has no cookies"),
    )

    with session_local() as db:
        with pytest.raises(ReportServiceError, match="storage state has no cookies") as exc:
            generate_report_artifact(db, audit_id=audit_id, report_type="full_report", storage_dir=tmp_path)

    assert exc.value.code == "reauth_required"


def test_persistence_writes_distinct_records_for_report_types(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    session_local = _build_session()
    audit_id = _seed_audit_data(session_local)
    monkeypatch.setattr("backend.reports.service.session_health", lambda: (True, "ok"))

    with session_local() as db:
        generate_report_artifact(db, audit_id=audit_id, report_type="full_report", storage_dir=tmp_path)
        generate_report_artifact(db, audit_id=audit_id, report_type="kp", storage_dir=tmp_path)
        rows = db.query(Report).filter(Report.audit_id == audit_id).order_by(Report.id.asc()).all()

    assert [row.type for row in rows] == ["full_report", "kp"]

