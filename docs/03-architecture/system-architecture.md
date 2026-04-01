# System Architecture

## Architecture Goal
Построить платформу, в которой deterministic ядро отвечает за сбор и анализ фактов, а генерация документов выполняется внешним AI-агентом по контролируемым промтам.

## High-level Flow
1. Intake: вход URL и параметров аудита.
2. Crawl: обход сайта и сбор технических данных.
3. Parse: извлечение блоков, сущностей и графа.
4. Analyze: coverage/contradictions/scoring/recommendations.
5. Package: сбор JSON-артефактов и prompt pack.
6. External AI: генерация документов для ролей.

## Logical Components
- Audit API: прием запросов на аудит и выдача статуса.
- Scheduler: планирование и управление очередями.
- Crawl Workers: загрузка страниц, link discovery.
- Render Workers: JS-рендеринг для динамических страниц.
- Extraction Engine: page_type + page_blocks extraction.
- Entity Builder: сущности и связи.
- Coverage Engine: проверка полноты.
- Contradiction Engine: поиск конфликтов.
- Scoring Engine: ECS/CS/ARS/LVI.
- Recommendation Engine: actionable рекомендации.
- Package Builder: сбор audit package + manifest.
- Prompt Generator: шаблоны промтов для документов.
- Storage Layer: хранение промежуточных и итоговых артефактов.
- Observability Layer: логи, метрики, трассировка этапов.

## Technology Reference
- Выбранный стек и альтернативы зафиксированы в `docs/03-architecture/technology-stack.md`.

## Data Boundaries
- Deterministic Core Boundary: от Intake до Package Builder.
- AI Boundary: генерация текстов документов за пределами ядра.
- Evidence Boundary: любой claim должен ссылаться на данные внутри package.

## Decision
- Принято: hybrid architecture (детерминированный анализ + внешний AI для текстов).
- Причина: контроль качества фактов, независимость от одной LLM, масштабируемость под разные агентские процессы.

## Alternatives
- Альтернатива 1: полностью встроенная генерация документов внутри платформы.
- Плюсы: единый контур.
- Минусы: сильная зависимость от конкретной модели, выше стоимость поддержки.

- Альтернатива 2: только технический crawl/analyze без document layer.
- Плюсы: меньше сложность MVP.
- Минусы: теряется ключевая коммерческая ценность продукта.

## Runet-first Constraints
- Приоритет правил и шаблонов для русскоязычных сайтов.
- Учет факторов релевантных для Яндекс/локальных AI экосистем.
- Локализованные словари и шаблоны блоков (цены, условия, юридические реквизиты).

## Facts
- `idea.md` фиксирует модель: crawler -> deterministic analysis -> package -> любой AI-агент.

## Assumptions
- Внешние AI-инструменты доступны через ручной или API handoff.

## Hypotheses
- Разделение контуров снизит риск регрессий от смены LLM-провайдера.

## Open Questions
- Нужен ли отдельный сервис оркестрации генерации документов внутри продукта на MVP-2.

## Traceability
- `idea.md`: блоки о независимости document generation, architecture-level разделении слоев, Runet-first позиционировании.
