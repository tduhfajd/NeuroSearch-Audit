# Schema Inventory

## Purpose

Схемы фиксируют versioned contracts между модулями deterministic core и итоговым `audit_package`.

## Versioning Rules

- Каждая схема имеет собственный `$id`.
- В package manifest фиксируется версия каждой схемы, использованной в аудите.
- Breaking changes повышают major-версию схемы и требуют обновления package contract.
- Нестабильные поля не допускаются без явного `experimental` статуса в схеме и manifest.

## MVP Schema Inventory

| File | Owner Module | Purpose | Status |
|---|---|---|---|
| `audit.schema.json` | M-01 Intake | audit record and lifecycle tracking | draft |
| `runtime_run_state.schema.json` | M-14 Runtime Orchestrator | persisted run state and stage transitions | draft |
| `manifest.schema.json` | M-13 Package Builder | package integrity and version manifest | draft |
| `crawl/visited_urls.schema.json` | M-03 Crawler | visited, skipped, and filtered URL lists plus crawl failures | draft |
| `crawl/fetch_log.schema.json` | M-03 Crawler | fetch attempts, statuses, timings, and frontier seed source (`submitted` / `sitemap` / `discovered`) | draft |
| `crawl/link_graph.schema.json` | M-03 Crawler | discovered edges and crawl graph | draft |
| `rendered_page.schema.json` | M-04 Renderer | rendered page artifact contract | draft |
| `render_plan.schema.json` | M-14 Runtime / M-04 Renderer | deterministic render-required assessment before browser fallback | draft |
| `render_fallback_report.schema.json` | M-14 Runtime / M-04 Renderer | bounded browser fallback execution report with failures and skipped candidates | draft |
| `technical_page.schema.json` | M-05 Technical Parser | normalized technical page features | draft |
| `page_blocks.schema.json` | M-06 Semantic Parser | aggregate semantic blocks document with per-page entries | draft |
| `entities.schema.json` | M-07 Entity Builder | extracted entities and evidence sources | draft |
| `normalized_facts.schema.json` | M-07 Entity Builder | normalized facts with evidence references | draft |
| `entity_graph.schema.json` | M-07 Entity Builder | graph edges and node references | planned |
| `coverage_report.schema.json` | M-08 Coverage Engine | coverage gaps, priorities, and impact | draft |
| `contradictions.schema.json` | M-09 Contradiction Engine | contradictory facts and sources | draft |
| `ai_readiness_scores.schema.json` | M-10 Scoring Engine | score outputs and summary | draft |
| `recommendations.schema.json` | M-11 Recommendation Engine | actionable normalized recommendations | draft |
| `legacy_factor_assessments.schema.json` | M-17 Legacy Factor Engine Rebuild | measurable legacy-style factor assessments derived from current package artifacts | draft |
| `legacy_index_scores.schema.json` | M-17 Legacy Factor Engine Rebuild | weighted legacy-style integral indices calculated from measurable factor assessments | draft |
| `review_brief.schema.json` | M-15 Delivery Review Builder | review-facing deterministic brief with crawl-quality summary derived from approved package | draft |
| `client_report_input.schema.json` | M-15 Delivery Export Builder | canonical adapter from approved package artifacts to legacy-style client report generation | draft |
| `client_report.schema.json` | M-15 Delivery Export Builder | legacy-style client report structure derived from `client_report_input.json` | draft |
| `expert_report.schema.json` | M-15 Delivery Export Builder | package-derived expert-report structure for richer client-facing narrative output | draft |
| `technical_client_report.schema.json` | M-16 Client Deliverables Rebuild | human-readable technical report for the client derived from the approved package | draft |
| `commercial_offer.schema.json` | M-15 Delivery Export Builder | package-derived commercial offer structure for presale and client discussion | draft |
| `technical_action_plan.schema.json` | M-15 Delivery Export Builder | package-derived implementation plan for technical and delivery teams | draft |
| `export_summary.schema.json` | M-15 Delivery Export Builder | lightweight operational export summary derived from approved package | draft |
| `export_backlog.schema.json` | M-15 Delivery Export Builder | normalized backlog export derived from approved package recommendations | draft |
| `handoff_event.schema.json` | M-16 Delivery Handoff Logger | append-only operational handoff event record | draft |
| `delivery_friction_report.schema.json` | M-17 Delivery Friction Evaluator | measured manual-friction and export-fit report | draft |
| `benchmark_case.schema.json` | M-18 Calibration Benchmark Set | benchmark case contract for pilot calibration review | draft |

## Directory Convention

```text
schemas/
  README.md
  audit.schema.json
  manifest.schema.json
  crawl/
    visited_urls.schema.json
    fetch_log.schema.json
    link_graph.schema.json
```

## Contract Rules

- Raw facts and derived outputs stay separated.
- Evidence-carrying objects must include source references.
- Stage-owned artifacts should be valid independently before package assembly.
- Schemas should prefer explicit required fields over permissive maps.

## Near-Term Follow-up

- Wire schema validation into `scripts/validate_all.py`.
- Add extraction and analysis schemas in Phases 03 and 04.
- Add sample artifact fixtures for contract validation.
