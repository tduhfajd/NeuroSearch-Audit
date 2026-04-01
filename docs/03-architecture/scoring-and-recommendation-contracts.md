# Scoring And Recommendation Contracts

## Goal

Зафиксировать baseline outputs для score-модели и нормализованных рекомендаций на основе coverage и contradictions.

## Score Contract

Score output contains:

1. `schema_version`
2. `audit_id`
3. `ruleset_version`
4. `page_scores[]`
5. `entity_scores[]`
6. `top_gaps[]`
7. `lead_value_index`

## Recommendation Contract

Recommendation output contains:

1. `schema_version`
2. `audit_id`
3. `recommendations[]` with `recommendation_id`, `related_findings`, `priority`, `effort`, `expected_impact`, `acceptance_criteria`

## Baseline Scoring Principles

- coverage score acts as the baseline for readiness;
- contradiction severity applies explicit penalties;
- `lead_value_index` remains explainable and rule-based.

## Baseline Recommendation Principles

- coverage recommendations remain block-oriented and explain missing business signals;
- contradiction recommendations should become more specific when the fact family is known;
- contact contradictions should instruct teams to choose one canonical value and propagate it across the affected site section.

## Package Location

```text
audit_package/<audit_id>/analysis/ai_readiness_scores.json
audit_package/<audit_id>/analysis/recommendations.json
```

## Follow-up

- Package builder and prompt generation should consume these outputs in Phase 05.
