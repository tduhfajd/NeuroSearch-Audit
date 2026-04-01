# Semantic Handoff

## Goal

Зафиксировать границу между `Go`-produced page artifacts и `Python` semantic layer, чтобы `page_blocks` генерировались из стабильных persisted inputs.

## Inputs To Semantic Layer

Semantic worker consumes:

1. `pages/technical/*.json`
2. optional `pages/rendered/*.json`
3. crawl-level URL context when needed for evidence references

## Ownership Boundary

- `Go` produces crawl, rendered, and technical artifacts.
- `Python` consumes those artifacts and produces `analysis/page_blocks.json`.
- Semantic extraction should not mutate upstream artifacts.

## Initial Handoff Shape

- primary required input: one technical page artifact;
- optional supplemental input: matching rendered page artifact;
- per-page output: one `PageBlocksDocument` with `page_type`, normalized blocks, deterministic factual signals, and evidence references;
- persisted package output: one aggregate `page_blocks.json` document with `pages[]`, where each item is a per-page `PageBlocksDocument`.

## Baseline Semantic Rules

- infer `page_type` from URL and technical signals;
- page typing should distinguish at least `homepage`, `category`, `product`, `contacts`, `delivery`, `return_policy`, `wholesale`, `article`, `service`, `generic`;
- infer `definition` from title or description presence;
- infer `faq` from schema hints;
- infer `process_steps` from multi-step heading structure;
- infer `contacts`, `pricing`, `terms`, `proof`, and `specs` from deterministic URL/title/heading patterns when obvious;
- emit deeper commerce/service expectations such as `availability`, `service_scope`, and `fulfillment` when URL, heading, and policy/payment signals make them explainable;
- consume `runet_signals` from technical extraction to emit `messengers`, `payment_options`, and `legal_trust` blocks when direct signals are present.
- emit deterministic per-page facts for already-structured technical signals such as phones, emails, messenger hints, payment hints, legal hints, and transport-policy metadata.

## Package Location

```text
audit_package/<audit_id>/analysis/page_blocks.json
```

## Aggregate Output Shape

The persisted package artifact is multi-page:

1. `schema_version`
2. `audit_id`
3. `pages[]`

This keeps runtime analysis package-shaped while preserving per-page semantic documents inside the aggregate.

## Follow-up

- Phase 04 should build entity extraction and coverage on top of `page_blocks`.
- Future semantic logic can get richer without changing the basic persisted handoff model.
