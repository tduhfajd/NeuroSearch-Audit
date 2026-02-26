---
status: testing
phase: 01-foundation
source:
  - .planning/phases/01-foundation/01-01-SUMMARY.md
  - .planning/phases/01-foundation/01-02-SUMMARY.md
  - .planning/phases/01-foundation/01-03-SUMMARY.md
started: 2026-02-26T13:38:36Z
updated: 2026-02-26T13:40:14Z
---

# Phase 1: Foundation — UAT

## Current Test

number: 1
name: Health endpoint contract
expected: |
  При открытом сервере запрос `GET /health` возвращает HTTP 200
  и JSON ровно `{"status":"ok"}`.
awaiting: next test selection

## Tests

### 1. Health endpoint contract
expected: `GET /health` -> `200` и `{"status":"ok"}`
result: pass (`code=200`, `body={"status":"ok"}`)

### 2. DB diagnostic endpoint
expected: `GET /health/db` -> `200` и статус из множества `ok/degraded`
result: pending

### 3. Root redirect behavior
expected: `GET /` (без follow redirects) -> `307` + `location: /static/index.html`
result: pending

### 4. Audits payload validation
expected: `POST /audits` с невалидным URL -> `422`
result: pending

### 5. Migration head state
expected: `alembic -c backend/db/migrations/alembic.ini current` -> `20260226_0001 (head)`
result: pending

### 6. Foundation table set
expected: В БД присутствуют таблицы `audits`, `pages`, `issues`, `reports`
result: pending

## Summary

total: 6
passed: 1
issues: 0
pending: 5
skipped: 0

## Gaps

<!-- YAML формат для потребления plan-phase --gaps -->
