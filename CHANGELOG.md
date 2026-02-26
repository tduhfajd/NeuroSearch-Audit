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

### Phase 2 — Crawler

- Added crawler core with URL normalization, strict-host scope, seed strategy (sitemap + homepage), depth/runtime limits, and retry/backoff.
- Added HTML extraction pipeline for `title`, `h1`, `meta_description`, `canonical`, `robots_meta`, `json_ld`, link sets, `word_count`, and `inlinks_count`.
- Added JS-render fallback heuristics and Playwright renderer wrapper.
- Added `robots.txt` / `sitemap.xml` checks and structured site-check status output.
- Added PageSpeed provider abstraction with Google API primary + Lighthouse fallback and top-10 selection by `inlinks_count`.
- Integrated `/audits` with DB-backed audit creation and crawl-job enqueue lifecycle.
- Added crawler persistence layer with batched idempotent upsert by (`audit_id`, `url`) and metadata updates in `audits.meta`.
- Added integration tests for enqueue/status lifecycle, persistence upsert behavior, and metadata/pagespeed storage.
- Added phase artifacts and evidence files:
  - `.planning/phases/02-crawler/02-01-SUMMARY.md`
  - `.planning/phases/02-crawler/02-02-SUMMARY.md`
  - `.planning/phases/02-crawler/02-03-SUMMARY.md`
  - `.planning/phases/02-crawler/02-01-HUMAN-VERIFY.md`
  - `.planning/phases/02-crawler/02-02-HUMAN-VERIFY.md`
  - `.planning/phases/02-crawler/02-03-HUMAN-VERIFY.md`
