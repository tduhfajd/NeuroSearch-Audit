# Data Contracts

## Contract Principles
- Версионирование схем (`schema_version`).
- Детерминированные поля и типы.
- Обязательная ссылочность источника (`source_urls`).
- Отделение raw facts от derived scores.
- Сквозной `audit_id` и согласованный lifecycle contract.

## C-001 page_blocks.json
- Назначение: агрегированный semantic handoff document с page-level blocks для всех страниц аудита.
- Обязательные поля:
1. `audit_id`
2. `schema_version`
3. `pages[]`
4. Each page entry includes `url`, `page_type`, `blocks[]`, `updated_at`

## C-002 entities.json
- Назначение: каталог сущностей.
- Обязательные поля:
1. `schema_version`
2. `audit_id`
3. `entities[]` with `entity_id`, `type`, `label`, `attributes`, `source_urls[]`

## C-002b normalized_facts.json
- Назначение: нормализованные факты для contradictions/coverage/scoring.
- Обязательные поля:
1. `schema_version`
2. `audit_id`
3. `facts[]` with `fact_id`, `entity_id`, `fact_type`, `value`, `evidence[]`

## C-003 entity_graph.json
- Назначение: связи между сущностями.
- Обязательные поля:
1. `nodes[]`
2. `edges[]` with `relation`, `from`, `to`, `evidence`
3. `graph_version`

## C-004 coverage_report.json
- Назначение: пробелы покрытия по правилам.
- Обязательные поля:
1. `coverage_ruleset`
2. `items[]` with `target`, `coverage_score`, `missing[]`, `priority`, `impact[]`
3. `summary`

## C-005 contradictions.json
- Назначение: конфликтующие факты.
- Обязательные поля:
1. `contradictions[]`
2. `type`
3. `severity`
4. `sources[]`
5. `risk[]`

## C-006 ai_readiness_scores.json
- Назначение: итоговые score по страницам/сущностям.
- Обязательные поля:
1. `schema_version`
2. `audit_id`
3. `ruleset_version`
4. `page_scores[]` with `url`, `scores{SEO,GEO,AEO,AIO,LEO}`, `factors`
5. `entity_scores[]`
6. `top_gaps[]`
7. `lead_value_index`

## C-007 recommendations.json
- Назначение: actionable рекомендации.
- Обязательные поля:
1. `schema_version`
2. `audit_id`
3. `recommendations[]` with `recommendation_id`, `related_findings[]`, `priority`, `effort`, `expected_impact`, `acceptance_criteria[]`

## C-008 manifest.json
- Назначение: описание целостности пакета.
- Обязательные поля:
1. `audit_id`
2. `created_at`
3. `ruleset_versions`
4. `schema_versions`
5. `files[]`

## C-000 audit.json
- Назначение: статус и жизненный цикл аудита.
- Обязательные поля:
1. `audit_id`
2. `submitted_url`
3. `status`
4. `stage_runs[]`
5. `package_status`

## C-009 prompts/*.md
- Назначение: инструкции внешнему AI для генерации документов.
- Обязательные секции:
1. Role
2. Audience
3. Allowed Inputs
4. Required Structure
5. Evidence Rules
6. No-fabrication Policy

## C-010 pages/rendered/*.json
- Назначение: persisted rendered page artifact for JS-heavy or runtime-dependent pages.
- Обязательные поля:
1. `audit_id`
2. `url`
3. `final_url`
4. `html`
5. `rendered_at`
6. `signals`

## C-011 pages/technical/*.json
- Назначение: normalized technical page features extracted from raw or rendered HTML.
- Обязательные поля:
1. `audit_id`
2. `url`
3. `source`
4. `extracted_at`
5. `meta`
6. `headings`
7. `schema_hints`
8. `runet_signals`

## C-012 runtime/<audit_id>/attempts/<nnn>/run_state.json
- Назначение: mutable execution state для одного attempt живого audit run.
- Обязательные поля:
1. `schema_version`
2. `audit_id`
3. `attempt`
4. `status`
5. `submitted_url`
6. `normalized_host`
7. `ruleset_version`
8. `started_at`
9. `updated_at`
10. `stages[]`
11. `transitions[]`

## C-013 exports/review_brief.json
- Назначение: deterministic review-facing summary derived from an approved package.
- Обязательные поля:
1. `schema_version`
2. `audit_id`
3. `package_status`
4. `lead_value_index`
5. `summary`
6. `crawl_quality`
7. `top_gaps`
8. `priority_pages`
9. `high_contradictions`
10. `priority_recommendations`
11. `evidence_sources`

## C-014 handoff/<audit_id>/handoff_log.jsonl
- Назначение: append-only operational log around approved package review and external AI handoff.
- Каждая запись обязана включать:
1. `event_id`
2. `audit_id`
3. `timestamp`
4. `event_type`
5. `actor`
6. `artifacts`

## C-015 crawl/fetch_log.json
- Назначение: журнал fetch attempts с evidence о том, как URL попал в crawl frontier.
- Обязательные поля для каждой записи:
1. `url`
2. `status`
3. `outcome`
4. `duration_ms`
5. `source` with one of `submitted`, `sitemap`, `discovered`

## C-016 render/render_plan.json
- Назначение: deterministic render-required assessment derived from raw crawl pages before browser fallback executes.
- Обязательные поля:
1. `schema_version`
2. `audit_id`
3. `generated_at`
4. `summary` with `total_pages`, `render_required_count`, `plain_fetch_count`
5. `candidates[]` with `url`, `reason`, `wait_selectors`, `signals`

## C-017 render/render_fallback_report.json
- Назначение: bounded execution report for browser fallback attempts.
- Обязательные поля:
1. `schema_version`
2. `audit_id`
3. `generated_at`
4. `max_rendered`
5. `attempted_count`
6. `rendered_count`
7. `failed_count`
8. `skipped_due_to_limit_count`
9. `entries[]` with `url`, `reason`, `status`, optional `error`

## Validation Rules
- Любой `high severity` finding без evidence -> contract violation.
- Несоответствие schema version -> package rejected.
- Пустые обязательные файлы -> package rejected.

## Lifecycle Reference
- Детализация статусов, package layout и retry semantics: `docs/03-architecture/audit-lifecycle.md`.
- Начальный inventory и первые JSON Schema: `schemas/README.md`, `schemas/audit.schema.json`, `schemas/manifest.schema.json`.
- Рендеринг и размещение rendered artifacts: `docs/03-architecture/rendering-contracts.md`.
- Технический parser и размещение outputs: `docs/03-architecture/technical-extraction-contracts.md`.
- Semantic handoff и `page_blocks` ownership: `docs/03-architecture/semantic-handoff.md`.
- Entity/fact normalization и ownership: `docs/03-architecture/entity-and-fact-contracts.md`.
- Coverage/contradictions ownership: `docs/03-architecture/coverage-and-contradiction-contracts.md`.
- Scoring/recommendation ownership: `docs/03-architecture/scoring-and-recommendation-contracts.md`.
- Runtime orchestration and `run_state.json`: `docs/03-architecture/runtime-execution-contracts.md`.

## Facts
- Набор ключевых JSON артефактов и их назначение зафиксирован в `idea.md`.

## Assumptions
- Имена файлов стабилизированы для MVP-1 и не требуют vendor-specific префиксов.

## Hypotheses
- Строгие контракты данных уменьшат стоимость интеграции новых AI-инструментов.

## Open Questions
- Нужны ли отдельные field-level схемы для отраслевых вертикалей (медицина, финансы).

## Traceability
- `idea.md`: секции с конкретными JSON (`page_blocks`, `entities`, `entity_graph`, `coverage_report`, `contradictions`, `ai_readiness_scores`) и принципом “dataset + prompts”.
