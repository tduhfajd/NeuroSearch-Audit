# Delivery Artifact Contracts

## Goal

Определить первый review-facing output для presale и delivery review так, чтобы он строился строго из approved package и не создавал второй mutable source of truth.

## Artifact Set

Для текущего deterministic delivery layer поддерживаются следующие artifact pairs / bridges:

1. `exports/review_brief.json`
2. `exports/review_brief.md`
3. `exports/client_report_input.json`
4. `exports/client_report.json`
5. `exports/client_report.md`
6. `exports/expert_report.json`
7. `exports/expert_report.md`
8. `exports/commercial_offer.json`
9. `exports/commercial_offer.md`
10. `exports/technical_action_plan.json`
11. `exports/technical_action_plan.md`
12. `deliverables/<audit_id>/client-report/client_report_<domain>.pdf`
13. `deliverables/<audit_id>/client-report/client_report_<domain>.html`
14. `deliverables/<audit_id>/client-report/client_report_<domain>.docx`

Оба артефакта:

- строятся только из approved package;
- являются package-derived outputs;
- не мутируют package facts;
- содержат только deterministic selection и templated rendering.

`client_report_input.json` и `client_report.*` подчиняются тем же правилам:

- не создают новый analytical source of truth;
- строятся поверх approved package artifacts;
- существуют как delivery/reporting projection layer;
- предназначены для миграции сильного legacy-style report output без возврата к старому sparse core.

Binary deliverables (`pdf/html/docx`) подчиняются отдельному правилу:

- они строятся только из approved `exports/client_report.md`;
- живут рядом с package в `deliverables/<audit_id>/client-report/`, а не внутри immutable `audit_package`;
- не считаются manifest-governed evidence artifacts.

## `review_brief.json`

Назначение:

- machine-readable summary для review и дальнейших delivery tooling layers;
- единый источник данных для markdown brief.

Обязательные поля:

1. `schema_version`
2. `audit_id`
3. `package_status`
4. `lead_value_index`
5. `summary`
6. `executive_summary`
7. `crawl_quality`
8. `top_gaps`
9. `action_plan`
10. `current_strengths`
11. `focus_areas`
12. `priority_pages`
13. `high_contradictions`
14. `priority_recommendations`
15. `evidence_sources`

### Summary

`summary` должен включать:

1. `page_count`
2. `high_contradiction_count`
3. `p0_coverage_targets`
4. `validate_status`

### Executive Summary

`executive_summary` должен включать:

1. `site_profile`
2. `health_band`
3. `overview`
4. `primary_risk`
5. `primary_opportunity`
6. `next_step`

Это deterministic narrative projection из package facts, а не AI-generated prose.

### Crawl Quality

`crawl_quality` должен включать:

1. `visited_url_count`
2. `skipped_url_count`
3. `filtered_url_count`
4. `fetch_failure_count`
5. `fetched_count`
6. `html_count`
7. `non_html_count`
8. `raw_page_count`
9. `submitted_count`
10. `sitemap_count`
11. `discovered_count`
12. `discovery_mode`
13. `protocol_duplication`
14. `warnings`

### Priority Pages

Каждая page entry связывает:

- `entity_id`
- `url`
- `page_type`
- `coverage_score`
- `missing`
- `scores`

Это review-facing projection, а не новый analysis result.

Selection rules:

- `priority_pages` is a capped review set, not the full list of analyzed pages;
- duplicate URL variants such as trailing-slash pairs should be deduplicated;
- homepage, category, contact, delivery, policy, and wholesale pages should outrank long tails of near-identical product pages when review priority is otherwise similar.
- repeated page types should be capped so the brief stays representative instead of being dominated by one template family.

### Top Gaps

`top_gaps` should be review-ranked, not alphabetically listed:

- gaps from higher-priority findings carry more weight;
- homepage, service, category, delivery, policy, and wholesale pages should influence ranking more than long tails of near-identical product pages;
- the brief should expose the most commercially meaningful recurring gaps first.

### Action Plan

`action_plan` is a compact review projection:

- deduplicated from recommendations by priority and first acceptance criterion;
- capped to keep review output readable;
- intended to answer "what would we do first" before the full recommendation list.

### Current Strengths

`current_strengths` highlights already-usable surfaces:

- deterministic statements only;
- derived from high-coverage pages on important page families;
- intended to keep the brief from reading like a pure defect list.

### Focus Areas

`focus_areas` groups recurring gaps by page family:

- `page_type`
- `page_count`
- `top_missing`

This gives the reviewer a compact view of where repeated work clusters instead of scanning page-by-page noise.

## `review_brief.md`

Назначение:

- human-readable brief для быстрого коммерческого или delivery review без custom tooling.

Структура:

1. `Audit ID`
2. `Package Status`
3. `Lead Value Index`
4. `Executive Summary`
5. `Crawl Quality`
6. `Top Gaps`
7. `What Already Works`
8. `Focus Areas`
9. `Action Plan`
10. `Priority Pages`
11. `High Contradictions`
12. `Priority Recommendations`
13. `Evidence Sources`

Markdown brief не должен:

- интерпретировать score вне package facts;
- придумывать narrative conclusion;
- скрывать contradictions или data gaps.

## `client_report_input.json`

Назначение:

- canonical bridge artifact between the current `audit_package` and the migrated legacy-style report layer;
- stable machine-readable input for richer client-facing report generation.

`client_report_input.json` должен включать:

1. `site`
2. `summary`
3. `indices`
4. `strengths`
5. `priority_areas`
6. `action_plan`
7. `constraints`
8. `evidence_sources`

Важно:

- он не заменяет `review_brief.json`;
- он существует как richer reporting adapter, а не как новый package truth layer.

## `client_report.json` and `client_report.md`

Назначение:

- deterministic client-facing report structure closer to the legacy NeuroSearch output style;
- basis for future PDF / HTML / DOCX rendering.

`client_report.json` должен:

- строиться из `client_report_input.json`;
- содержать section-oriented report structure;
- не повторно анализировать сайт и не вводить новые факты.

`client_report.md` должен:

- быть шаблонным human-readable rendering из `client_report.json`;
- сохранять client-facing структуру: ключевой вывод, что оценивалось, индексы, сильные стороны, приоритетные зоны, план действий, ограничения.

## `client_report.pdf/html/docx`

Назначение:

- branded client deliverables для review, отправки клиенту и редактируемого handoff;
- presentation layer поверх `client_report.md`, а не новый аналитический источник данных.

Правила:

- сборка допускается только из approved package;
- build flow не должен парсить markdown обратно в JSON;
- PDF/HTML/DOCX generation использует in-repo `reportgen` templates/assets и `pandoc`-based renderer;
- deliverables могут быть пересобраны повторно без мутации package facts.

## `expert_report.json` and `expert_report.md`

Назначение:

- richer client-facing narrative document closer to the legacy `expert_report.md`;
- package-derived bridge from the current evidence core to executive/client explanation.

`expert_report.json` должен:

- строиться только из approved package artifacts and already-derived exports;
- сохранять section-oriented structure без повторного анализа сайта;
- оставаться schema-backed optional export.

`expert_report.md` должен:

- быть deterministic rendering из `expert_report.json`;
- сохранять legacy-style narrative sections: что важно руководителю, где теряется результат, ключевые недостатки, план 30/60/90, ценность для клиента, ограничения, измерение эффекта.

## `commercial_offer.json/md` and `technical_action_plan.json/md`

Назначение:

- перенести сильные legacy client-document workflows для presale and delivery execution;
- давать package-derived документы для обсуждения пакета работ и для выполнения командой.

`commercial_offer.json/md` должен:

- строиться из approved package delivery exports и recommendations;
- описывать пакеты услуг, рекомендуемый стартовый пакет, этапность и клиентские предпосылки;
- не обещать результат вне подтвержденных package facts.

`technical_action_plan.json/md` должен:

- строиться из approved package recommendations, priority pages, and review outputs;
- давать task-oriented implementation plan для технической команды;
- содержать target pages, implementation steps, definition of done, verification, and expected effect.

## Generation Flow

```text
approved package
  -> load manifest + analysis artifacts
  -> build review_brief.json
  -> render review_brief.md from review_brief.json
  -> build client_report_input.json
  -> build client_report.json
  -> render client_report.md from client_report.json
  -> build expert_report.json
  -> render expert_report.md from expert_report.json
  -> build commercial_offer.json
  -> render commercial_offer.md from commercial_offer.json
  -> build technical_action_plan.json
  -> render technical_action_plan.md from technical_action_plan.json
  -> render client_report.pdf/html/docx from client_report.md
```

Правила:

- generation допускается только при `manifest.stage_status.validate == completed`;
- все массивы сортируются детерминированно;
- markdown строится шаблонно из уже выбранных полей.

## Relationship To Existing Exports

- `exports/summary.json` остается lightweight operational handoff.
- `exports/backlog.json` остается delivery-import handoff.
- `exports/review_brief.*` становится human-review handoff.
- `exports/client_report_input.json` становится canonical migration bridge for richer reporting.
- `exports/client_report.*` становится deterministic client-facing report layer for migrated legacy-style delivery.

## Traceability

- Schema: [review_brief.schema.json](/Users/vadimevgrafov/neurosearch-analyzer/schemas/review_brief.schema.json)
- Schema: [client_report_input.schema.json](/Users/vadimevgrafov/neurosearch-analyzer/schemas/client_report_input.schema.json)
- Schema: [client_report.schema.json](/Users/vadimevgrafov/neurosearch-analyzer/schemas/client_report.schema.json)
- Export boundaries: [export-boundaries.md](/Users/vadimevgrafov/neurosearch-analyzer/docs/03-architecture/export-boundaries.md)
