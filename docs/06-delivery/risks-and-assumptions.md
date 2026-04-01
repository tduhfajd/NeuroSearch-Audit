# Risks and Assumptions

## Key Risks

### R-001 Недостаточная полнота краулинга
- Severity: high.
- Impact: пропуск критичных страниц и ложные выводы.
- Mitigation: fallback стратегии discovery (sitemap/internal links/nav/API hints), coverage monitoring.

### R-002 Низкое качество нормализации фактов
- Severity: high.
- Impact: ложные contradictions и недоверие к отчету.
- Mitigation: rule tuning, тест-корпус, ручная валидация high severity.

### R-003 Зависимость от качества внешнего AI
- Severity: medium.
- Impact: нестабильный стиль/структура документов.
- Mitigation: строгий prompt spec + evidence validator + шаблоны.

### R-004 Переусложнение MVP
- Severity: medium.
- Impact: срыв сроков и потери фокуса.
- Mitigation: фиксировать scope MVP-1, откладывать non-critical интеграции.

### R-005 Недостаточная адаптация под Runet
- Severity: high.
- Impact: нерелевантные рекомендации для целевого рынка.
- Mitigation: Runet-first ruleset, RU-паттерны контента, пилоты на локальных сайтах.

### R-006 Недоказательные claims в документах
- Severity: high.
- Impact: репутационные и коммерческие риски.
- Mitigation: evidence-first policy, quality gate на source coverage.

## Assumptions
- A-001: у команды есть доступ к внешним AI-агентам для генерации документов.
- A-002: MVP-1 реализуется rule-based без необходимости ML-моделей.
- A-003: клиент принимает этапный формат внедрения (MVP-1 -> MVP-2).
- A-004: состав из 5 документов достаточно покрывает пресейл и delivery процесс.

## Validation Plan for Assumptions
- A-001: проверка на 2-3 AI-провайдерах.
- A-002: пилот на наборе Runet-сайтов.
- A-003: интервью с 3-5 агентствами.
- A-004: пилотное использование пакета на реальных лидах.

## Facts
- Риски качества краулинга, contradictions и AI-generate слоя прямо следуют из `idea.md`.

## Hypotheses
- Жесткие quality gates компенсируют вариативность внешних AI-инструментов.

## Open Questions
- Какие юридические/комплаенс требования нужны для хранения клиентских пакетов.
- Как формализовать порог “достаточной полноты” crawl coverage.

## Traceability
- `idea.md`: блоки о недостатках классического краулинга, роли contradictions, независимости генерации от конкретного AI и приоритете Runet.
