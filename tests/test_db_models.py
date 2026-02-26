from backend.db.models import Base


def test_expected_tables_are_declared() -> None:
    assert set(Base.metadata.tables.keys()) == {"audits", "pages", "issues", "reports"}


def test_audits_table_has_required_columns() -> None:
    audits = Base.metadata.tables["audits"]
    assert "status" in audits.c
    assert "meta" in audits.c
    assert "seo_score" in audits.c
    assert "avri_score" in audits.c
    assert audits.c.url.nullable is False


def test_pages_table_has_ai_and_schema_fields() -> None:
    pages = Base.metadata.tables["pages"]
    assert "json_ld" in pages.c
    assert "ai_scores" in pages.c
    assert "audit_id" in pages.c


def test_foreign_keys_are_present() -> None:
    pages = Base.metadata.tables["pages"]
    issues = Base.metadata.tables["issues"]
    reports = Base.metadata.tables["reports"]

    assert any(fk.target_fullname == "audits.id" for fk in pages.c.audit_id.foreign_keys)
    assert any(fk.target_fullname == "audits.id" for fk in issues.c.audit_id.foreign_keys)
    assert any(fk.target_fullname == "audits.id" for fk in reports.c.audit_id.foreign_keys)
