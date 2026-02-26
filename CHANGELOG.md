# Changelog

## 2026-02-26

### Phase 1 — Foundation

- Added project bootstrap files: `pyproject.toml`, `.env.example`, `.gitignore`.
- Implemented FastAPI skeleton with `/`, `/health`, `/health/db`, and `/audits` skeleton routes.
- Added SQLAlchemy models and sync DB session layer for `audits`, `pages`, `issues`, `reports`.
- Added Alembic configuration and initial migration `20260226_0001`.
- Added local runbook in `README.md` (Homebrew primary, Docker fallback) and `docker-compose.yml` for PostgreSQL.
- Added tests for API foundation, DB models/migrations, health contract, and smoke startup wiring.
- Added phase artifacts and evidence files:
  - `.planning/phases/01-foundation/01-01-SUMMARY.md`
  - `.planning/phases/01-foundation/01-02-SUMMARY.md`
  - `.planning/phases/01-foundation/01-03-SUMMARY.md`
  - `.planning/phases/01-foundation/01-01-HUMAN-VERIFY.md`
  - `.planning/phases/01-foundation/01-02-HUMAN-VERIFY.md`
  - `.planning/phases/01-foundation/01-03-HUMAN-VERIFY.md`
