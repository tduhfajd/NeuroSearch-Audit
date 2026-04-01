# Technical Extraction Contracts

## Goal

Зафиксировать versioned output для технического парсинга страниц, чтобы downstream analysis получал стабильный набор metadata и structural hints.

## Input Contract

Technical parser consumes:

1. `audit_id`
2. `url`
3. `html`
4. `source` (`crawl` or `rendered`)
5. transport header context such as `Strict-Transport-Security`

## Output Contract

Technical page artifact contains:

1. `schema_version`
2. `audit_id`
3. `url`
4. `source`
5. `extracted_at`
6. `title`
7. `meta.description`
8. `headings.h1[]`
9. `headings.h2[]`
10. `canonical_url`
11. `robots`
12. `schema_hints[]`
13. `runet_signals` with bounded `phones`, `emails`, `messenger_hints`, `payment_hints`, `legal_hints`
14. `transport_signals.strict_transport_security`
15. `transport_signals.mixed_content_urls[]`

## Package Location

```text
audit_package/<audit_id>/pages/technical/<normalized-page>.json
```

## Parser Behavior

- Missing fields should degrade to empty strings or empty arrays, not parser failure.
- Extraction remains deterministic and rule-based.
- Rendered pages may be preferred over raw HTML when a render artifact exists.
- Raw crawl artifacts remain preserved; rendered HTML only overrides extraction input for the URLs explicitly chosen by the render plan.
- Mixed-content detection is bounded and evidence-oriented; the artifact stores the first deterministic set of detected `http://` asset references on HTTPS pages.

## Related Artifacts

- [technical_page.schema.json](/Users/vadimevgrafov/neurosearch-analyzer/schemas/technical_page.schema.json)
- [Rendering Contracts](/Users/vadimevgrafov/neurosearch-analyzer/docs/03-architecture/rendering-contracts.md)
- [Data Contracts](/Users/vadimevgrafov/neurosearch-analyzer/docs/03-architecture/data-contracts.md)
