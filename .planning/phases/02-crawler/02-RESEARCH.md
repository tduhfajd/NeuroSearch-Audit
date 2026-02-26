# Phase 2: Crawler - Research

**Date:** 2026-02-26
**Scope:** Planning research for crawler phase (no implementation)

## Research Need Assessment

External/domain research is not required for this phase.

Reasons:
- Stack and architecture are already fixed in project documents:
  - Scrapy 2.x + Playwright (Chromium)
  - FastAPI backend
  - PostgreSQL + SQLAlchemy models already prepared in Phase 1
- Phase 2 decisions are finalized in `.planning/phases/02-crawler/02-CONTEXT.md`.
- Requirements and success criteria are explicit in `.planning/ROADMAP.md` and `.planning/REQUIREMENTS.md`.

## Practical Planning Findings

- The phase is best split into 3 vertical plans:
  1. Crawl core + parser extraction (CRL-01, CRL-02 base)
  2. JS rendering + robots/sitemap + PageSpeed providers (CRL-03, CRL-04, CRL-05)
  3. API orchestration + persistence integration + end-to-end verification (all criteria closure)
- Wave strategy for safe parallelism:
  - Wave 1: two independent foundations (core crawler and external-check/provider layer)
  - Wave 2: integration plan that depends on both

## Risks to Capture in Plans

- Local environment may lack ready PageSpeed API key: fallback path via Lighthouse CLI is mandatory.
- Playwright usage can be expensive; heuristic escalation criteria must be explicit and testable.
- Crawl throughput can destabilize local Mac if concurrency/batching defaults are too aggressive.
- DB writes must be idempotent by (`audit_id`, `url`) to avoid duplicate pages on retry.

## Non-Goals in This Phase

- No analyzer logic (issues/priorities/scoring).
- No AI Bridge calls.
- No report generation logic.

---

*Result: ready for Phase 2 plan authoring with no additional external research.*
