# Entity And Fact Contracts

## Goal

Зафиксировать первый analysis-layer contract, который превращает `page_blocks` в нормализованные сущности и факты с привязкой к evidence.

## Inputs

Analysis normalization consumes:

1. `analysis/page_blocks.json`
2. source URLs and evidence references already embedded in page blocks

## Outputs

### `entities.json`

- one or more normalized entities;
- stable `entity_id`;
- `type`, `label`, `attributes`, `source_urls`.

### `normalized_facts.json`

- normalized facts tied to `entity_id`;
- explicit `fact_type` and `value`;
- evidence references preserved from upstream artifacts.

## Ownership

- `python/analysis` owns normalization from semantic outputs into entities and facts.
- Downstream coverage, contradiction, and scoring layers should consume normalized facts rather than raw page blocks whenever possible.

## Baseline Normalization Rules

- every page creates at least one `page` entity;
- `page_type` becomes a normalized fact;
- each semantic block presence becomes a fact tied to the page entity;
- deterministic factual signals from semantic handoff (contacts, messenger/payment/legal hints, transport-policy values) also become normalized facts tied to the same page entity;
- evidence flows through unchanged from `page_blocks`.

## Package Location

```text
audit_package/<audit_id>/analysis/entities.json
audit_package/<audit_id>/analysis/normalized_facts.json
```

## Follow-up

- Coverage and contradiction engines should use normalized facts as the first common substrate.
- Later phases may introduce richer entity types without changing the baseline contracts.
