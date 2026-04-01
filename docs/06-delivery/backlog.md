# Backlog

## Priority Legend
- P0: критично для MVP и клиентской ценности.
- P1: важно для коммерческого запуска.
- P2: улучшения качества/масштабирования.
- P3: отложенные инициативы.

## MVP-1 Backlog

### BL-001 (P0) Intake + Audit Lifecycle
- Description: создать запуск аудита, `audit_id`, статусы этапов.
- Acceptance Criteria:
1. Можно запустить аудит по URL.
2. Видны статусы этапов до завершения package.

### BL-002 (P0) Crawl Queue + URL Discovery
- Description: реализовать очередь обхода, visited set, ограничения глубины.
- Acceptance Criteria:
1. Повторные URL не обходятся повторно.
2. Присутствуют логи причин пропусков.

### BL-003 (P0) Semantic Blocks Extraction
- Description: выделить page_type и базовые блоки для Runet-first rules.
- Acceptance Criteria:
1. Для каждой страницы сохраняется page_type.
2. Для каждого блока хранится presence/confidence/evidence.

### BL-004 (P0) Entities + Entity Graph
- Description: извлечь ключевые сущности и связи.
- Acceptance Criteria:
1. Поддержаны типы сущностей MVP-1.
2. Связи имеют source evidence.

### BL-005 (P0) Coverage Report
- Description: сформировать coverage gaps и score 0..1.
- Acceptance Criteria:
1. Для каждого target есть coverage score.
2. У gaps есть priority + impact.

### BL-006 (P0) Contradictions Engine
- Description: выявление конфликтов по ключевым классам фактов.
- Acceptance Criteria:
1. Для contradictions есть severity и sources.
2. High severity маркируются как P0.

### BL-007 (P0) ARS/LVI Scoring
- Description: расчет score моделей MVP.
- Acceptance Criteria:
1. Выдаются SEO/GEO/AEO/AIO/LEO score per page.
2. LVI рассчитывается для пресейл-приоритизации.

### BL-008 (P0) Recommendation Generator
- Description: шаблонные actionable рекомендации.
- Acceptance Criteria:
1. Каждая рекомендация связана с finding.
2. Есть acceptance criteria для внедрения.

### BL-009 (P0) Prompt Pack Generator
- Description: 5 промтов под пакет документов.
- Acceptance Criteria:
1. Каждый промт с секциями role/audience/inputs/structure/evidence.
2. В каждом промте есть no-fabrication policy.

### BL-010 (P0) Package Builder + Manifest
- Description: собрать единый audit package.
- Acceptance Criteria:
1. Полный набор обязательных файлов.
2. Валидация целостности перед выдачей.

## MVP-2 Backlog

### BL-011 (P1) Advanced Normalization
- Description: усилить нормализацию цен, сроков, гео.
- Acceptance Criteria:
1. Снижение ложных contradictions на пилотах.

### BL-012 (P1) AEO/LEO Signals
- Description: добавить сигналы “краткий ответ”, таблицы сравнения, параметры выбора.
- Acceptance Criteria:
1. Улучшенные AEO/LEO score отражаются в отчетах.

### BL-013 (P1) Baseline Delta Report
- Description: сравнение аудитов до/после внедрения.
- Acceptance Criteria:
1. Отчет показывает прирост score и закрытые gaps.

### BL-014 (P2) Task Tracker Export
- Description: экспорт задач в Jira/GitLab формат.
- Acceptance Criteria:
1. Задачи содержат evidence и acceptance criteria.

## Post-MVP Backlog
- BL-015 (P2): CRM integration.
- BL-016 (P2): batch audit processing.
- BL-017 (P2): отраслевые ruleset.
- BL-018 (P3): white-label template engine.

## Facts
- `idea.md` определяет приоритет MVP-1 как fastest value и MVP-2 как усиление GEO/AEO/LEO.

## Assumptions
- Sequence backlog соответствует зависимости модулей deterministic core.

## Hypotheses
- Запуск P0 набора уже даст коммерчески полезный пресейл pipeline.

## Open Questions
- Какие задачи из P1 нужно подтянуть в MVP-1 под пилотного клиента.

## Traceability
- `idea.md`: секции с MVP-1/MVP-2, coverage/contradictions, prompt pack и фокус на “быстро продает”.
