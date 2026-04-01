# Modules and Responsibilities

## Module Catalog

### M-01 Intake
- Ответственность: принять `audit_request` и валидационные параметры.
- Вход: URL, лимиты, режимы анализа.
- Выход: `audit_id`, старт задания.

### M-02 Scheduler/Queue
- Ответственность: распределить URL по воркерам, контролировать retry/timeout.
- Вход: стартовые URL и политики обхода.
- Выход: очередь crawl задач.

### M-03 Crawler
- Ответственность: скачать страницы, извлечь ссылки, поддержать глубину и visited set.
- Вход: queue jobs.
- Выход: raw page artifacts + link graph edges.

### M-04 Renderer
- Ответственность: рендер динамических страниц и фиксация API/network hints.
- Вход: URL с признаком JS-heavy.
- Выход: rendered DOM snapshot.

### M-05 Technical Parser
- Ответственность: извлечь title/meta/headings, canonical, robots, schema hints.
- Вход: raw/rendered page.
- Выход: technical feature set.

### M-06 Semantic Parser
- Ответственность: определить `page_type` и блоки `definition/process/pricing/faq/proof/terms/contacts/comparison`.
- Вход: parsed DOM/text blocks.
- Выход: `page_blocks.json`.

### M-07 Entity Builder
- Ответственность: извлечь entities и построить entity graph.
- Вход: page blocks + technical hints.
- Выход: `entities.json`, `entity_graph.json`.

### M-08 Coverage Engine
- Ответственность: вычислить полноту по ruleset.
- Вход: entities + blocks + page types.
- Выход: `coverage_report.json`.

### M-09 Contradiction Engine
- Ответственность: выявить конфликтующие факты.
- Вход: facts per URL/entity.
- Выход: `contradictions.json`.

### M-10 Scoring Engine
- Ответственность: рассчитать ECS/CS/ARS/LVI.
- Вход: outputs M-08/M-09 + technical signals.
- Выход: `ai_readiness_scores.json` + summary.

### M-11 Recommendation Engine
- Ответственность: выпустить рекомендации и приоритеты внедрения.
- Вход: findings + scores.
- Выход: `recommendations.json`.

### M-12 Prompt Generator
- Ответственность: сформировать промты для 5 документов.
- Вход: package manifest + outputs M-06..M-11.
- Выход: `prompts/*.md`.

### M-13 Package Builder
- Ответственность: собрать целостный пакет артефактов.
- Вход: все outputs модулей.
- Выход: `audit_package/<audit_id>/`.

### M-14 Evidence Validator
- Ответственность: проверить ссылочную целостность claims/facts.
- Вход: findings/recommendations/prompts.
- Выход: quality report, gate pass/fail.

### M-15 Observability
- Ответственность: метрики, логи, трассировка этапов.
- Вход: события модулей.
- Выход: operational dashboards/log streams.

## Module Dependencies
- M-03 зависит от M-02.
- M-06 зависит от M-03/M-04/M-05.
- M-08/M-09 зависят от M-06/M-07.
- M-10 зависит от M-08/M-09.
- M-11 зависит от M-10.
- M-12 зависит от M-11 и package manifest.
- M-14 проверяет M-11/M-12 перед финальной выдачей M-13.

## Ownership Model
- Product/Data: правила блоков, сущностей, scoring.
- Engineering: runtime, queueing, storage, observability.
- Delivery/Presale: шаблоны отчетов и КП.

## Facts
- `idea.md` описывает связку crawler/parser/scoring/prompt generator и пакет документов.

## Assumptions
- Evidence Validator реализуется как отдельный модуль, а не функция Prompt Generator.

## Hypotheses
- Выделение Renderer в отдельный модуль повысит стабильность core crawler.

## Open Questions
- Нужен ли отдельный модуль для нормализации геоданных РФ в MVP-1.

## Traceability
- `idea.md`: блоки о модульной архитектуре, semantic crawling, entity graph и документ-ориентированной выдаче.
