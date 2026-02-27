from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db import session as db_session_module
from backend.db.models import Audit, Base
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


def _seed_audit(session_local: sessionmaker) -> int:
    with session_local() as db:
        audit = Audit(
            url="https://example.com",
            client_name="Example LLC",
            status="completed",
            crawl_depth=200,
            pages_crawled=42,
            seo_score=77.5,
            avri_score=63.0,
            meta={"progress": 100},
            created_at=datetime.utcnow(),
        )
        db.add(audit)
        db.commit()
        db.refresh(audit)
        return audit.id


def test_get_audit_by_id_returns_audit_payload() -> None:
    client, session_local = _build_client_and_session()
    try:
        audit_id = _seed_audit(session_local)
        response = client.get(f"/audits/{audit_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == audit_id
    assert payload["url"] == "https://example.com"
    assert payload["seo_score"] == 77.5
    assert payload["avri_score"] == 63.0
    assert payload["status"] == "completed"


def test_get_audit_by_id_returns_404_when_missing() -> None:
    client, _ = _build_client_and_session()
    try:
        response = client.get("/audits/999")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Audit not found"
