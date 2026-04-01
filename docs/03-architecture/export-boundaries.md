# Export Boundaries

## Goal

Определить минимальные и безопасные export surfaces для пилотного использования без прямой интеграции с CRM или task tracker.

## Principles

- Export only from an approved package.
- Export payloads must remain package-scoped and reproducible.
- No export may invent or reinterpret facts beyond package artifacts.

## Pilot Export Surfaces

### 1. `exports/summary.json`

Purpose:

- lightweight handoff into presale or CRM-adjacent workflows;
- summarize audit status, lead value, top gaps, and major contradictions.

Fields:

1. `audit_id`
2. `status`
3. `lead_value_index`
4. `top_gaps`
5. `high_contradictions`
6. `package_status`

### 2. `exports/backlog.json`

Purpose:

- lightweight handoff into delivery or task-tracker import flows.

Fields:

1. `audit_id`
2. `items[]` with `recommendation_id`, `priority`, `expected_impact`, `acceptance_criteria`, `related_findings`

### 3. `exports/review_brief.json` and `exports/review_brief.md`

Purpose:

- human-review handoff for presale or delivery leads;
- compact review artifact that stays grounded in approved package facts.

Fields:

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

## Non-Goals

- direct CRM writes;
- Jira/GitLab API integration;
- sync or two-way state management;
- package mutation after export.

## Preconditions

- package approval gate has passed;
- `manifest.json`, `ai_readiness_scores.json`, `contradictions.json`, and `recommendations.json` are present.

## Follow-up

- If pilot usage proves these exports useful, Phase `06-03` or a future milestone can turn them into live integrations.
