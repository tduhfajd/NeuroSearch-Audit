# Coverage and Contradictions

## Coverage Framework

### Page Type Rules (MVP)
- service: definition, process_steps, terms, proof, pricing, faq, contacts/cta.
- product: specs, pricing, delivery/payment/returns, availability, reviews, faq, comparison.
- category: filters/attributes, explanatory text, comparison blocks, category links, faq.
- article: short answer, structured headings, lists/tables, summary, internal links.

### Coverage Result Structure
- Target: URL или entity.
- Score: 0..1.
- Missing Blocks: список обязательных пробелов.
- Priority: P0/P1/P2.
- Impact: SEO/GEO/AEO/AIO/LEO/conversion.
- Evidence: URL + fragment reference.

## Contradiction Framework

### Contradiction Types
- price_conflict
- terms_conflict
- timeline_conflict
- geo_conflict
- contact_conflict

### Severity Policy
- high: цены, гарантии, договорные условия.
- medium: сроки, география, контакты.
- low: формулировки и несильные расхождения.

### Detection Logic
1. Нормализовать факты одного типа (например цены).
2. Сгруппировать по сущности/теме.
3. Сравнить несовместимые значения.
4. Выдать contradiction с severity и source URLs.

## Prioritization Matrix
- P0: high contradiction или критичный coverage gap на money pages.
- P1: средний риск или частичное покрытие ключевых сущностей.
- P2: улучшения полноты без блокирующего риска.

## Quality Constraints
- Любой contradiction без минимум 2 источников не публикуется.
- Любой gap без привязки к ruleset не публикуется.
- Для каждого high-risk finding обязателен remediation suggestion.

## Facts
- `idea.md` детально задает coverage rules, contradictions и их влияние на AIO/доверие/продажи.

## Assumptions
- money pages можно определять по шаблонам URL и page_type.

## Hypotheses
- Явное разделение gaps и contradictions упростит переговоры “что делаем сначала”.

## Open Questions
- Нужны ли отраслевые severity-правила, отличные от базовых.

## Traceability
- `idea.md`: секции “Coverage rules”, “Contradiction score”, “влияние на GEO/AEO/AIO/LEO”, приоритизация работ.
