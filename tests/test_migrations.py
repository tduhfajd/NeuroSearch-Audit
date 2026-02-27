from pathlib import Path


def test_initial_migration_file_exists() -> None:
    path = Path("backend/db/migrations/versions/20260226_0001_initial_foundation.py")
    assert path.exists()


def test_pages_unique_migration_file_exists() -> None:
    path = Path("backend/db/migrations/versions/20260227_0002_pages_audit_url_unique.py")
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "uq_pages_audit_url" in content


def test_alembic_env_and_ini_exist() -> None:
    assert Path("backend/db/migrations/env.py").exists()
    assert Path("backend/db/migrations/alembic.ini").exists()
