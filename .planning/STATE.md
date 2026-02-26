# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-26)

**Core value:** Аудит сайта → готовый PDF-отчёт с КП за один запуск
**Current focus:** Phase 2 — Crawler

## Current Position

Phase: 2 of 7 (Crawler)
Plan: 2 of 3 in current phase
Status: In progress
Last activity: 2026-02-26 — Выполнен plan 02-02 (JS fallback + robots/sitemap + pagespeed providers).

Progress: [███░░░░░░░] 28%

## Performance Metrics

**Velocity:**
- Total plans completed: 5
- Average duration: 9.0 minutes
- Total execution time: 0.7 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Foundation | 3/3 | 25 min | 8.3 min |
| 2. Crawler | 2/3 | 20 min | 10 min |
| 3. Analyzer | 0/8 | - | - |
| 4. AI Bridge | 0/7 | - | - |
| 5. Dashboard | 0/6 | - | - |
| 6. Reports | 0/7 | - | - |
| 7. Polish | 0/5 | - | - |

## Accumulated Context

### Decisions

Решения логируются в PROJECT.md Key Decisions.
Недавние решения, влияющие на текущую работу:

- **Phase 2 crawler strategy** — queue-based orchestration, sitemap+homepage hybrid discovery, strict host default
- **Extraction baseline** — title/h1/meta/canonical/robots/jsonld/links/word_count/inlinks_count implemented
- **JS/checks/pagespeed baseline** — Playwright heuristic fallback, robots/sitemap checks, PageSpeed API primary + Lighthouse fallback

### Pending Todos

- Интегрировать API/RQ/DB persistence end-to-end (plan 02-03)
- Получить Google PageSpeed API key перед production-like прогонами CRL-05

### Blockers/Concerns

- ⚠️ **AI Bridge хрупкость**: ChatGPT может изменить UI — нужна стратегия обновления селекторов
- ⚠️ **Rate limit ChatGPT Plus**: ~50 сообщений/3ч — аудит 10 страниц + генерация отчёта ~15 запросов, это ок; но нельзя параллелить несколько аудитов одновременно
- ⚠️ **Кириллица в PDF**: WeasyPrint требует правильной конфигурации шрифтов — проверить на Phase 6

## Session Continuity

Last session: 2026-02-26
Stopped at: Завершён plan 02-02, следующий шаг — plan 02-03 (API + queue + persistence integration)
Resume file: .planning/phases/02-crawler/02-02-SUMMARY.md
