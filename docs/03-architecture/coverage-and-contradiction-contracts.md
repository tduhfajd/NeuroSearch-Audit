# Coverage And Contradiction Contracts

## Goal

Зафиксировать first-pass outputs для coverage gaps и contradictions на основе normalized facts.

## Coverage Contract

Coverage report contains:

1. `schema_version`
2. `audit_id`
3. `coverage_ruleset`
4. `items[]` with `target`, `coverage_score`, `missing`, `priority`, `impact`, `evidence`
5. `summary`

## Contradiction Contract

Contradictions report contains:

1. `schema_version`
2. `audit_id`
3. `contradictions[]` with `contradiction_id`, `entity_id`, `type`, `severity`, `sources`, `risk`

## Baseline Rules

- coverage evaluates required blocks per `page_type`;
- coverage may infer a coarse site profile such as `service`, `ecommerce`, or `mixed` from the audited page set and use it to tighten priorities and impact labels;
- policy-like pages (`delivery`, `return_policy`, `contacts`) and commerce pages (`product`, `category`, `wholesale`) may carry different critical blocks than content pages;
- deeper commerce/service rules may require `availability`, `service_scope`, or `fulfillment` when the page family implies offer scope, stock/ordering clarity, or handoff expectations;
- Runet-oriented rules may tighten coverage on `contacts`, `delivery`, `return_policy`, `wholesale`, `homepage`, and commerce pages when `messengers`, `payment_options`, or `legal_trust` signals are expected;
- contradictions are published only when at least two independent sources disagree;
- severity remains explainable and tied to contradiction type;
- contradiction risk can now vary by fact family, for example `contact` conflicts emphasize `lead_quality` while `timeline` or `terms` conflicts emphasize `operations` and trust.
- contradictions may use different scopes depending on fact family:
  - page-local for `price`, `timeline`, and `terms`;
  - site-wide for canonical contact signals such as `contact_phone` and `contact_email`.

## Package Location

```text
audit_package/<audit_id>/analysis/coverage_report.json
audit_package/<audit_id>/analysis/contradictions.json
```

## Follow-up

- Scoring and recommendation logic should consume these outputs in Phase 04-03.
