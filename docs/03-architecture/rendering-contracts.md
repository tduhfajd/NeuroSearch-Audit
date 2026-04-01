# Rendering Contracts

## Goal

Зафиксировать изолированный контракт рендеринга для страниц, где raw crawl недостаточен из-за JS-heavy поведения или runtime-generated content.

## Rendering Principles

- Рендеринг является отдельным этапом после crawl, а не частью fetch loop.
- Решение о рендеринге принимается через явные правила, а не автоматически для всех страниц.
- Rendered artifacts сохраняются отдельно от raw crawl outputs под `pages/rendered/`.

## Render Job Contract

Минимальные поля:

1. `audit_id`
2. `url`
3. `reason`
4. `wait_selectors[]`

## Render Result Contract

Минимальные поля:

1. `schema_version`
2. `audit_id`
3. `url`
4. `render_mode`
5. `final_url`
6. `html`
7. `rendered_at`
8. `signals`

## Package Location

```text
audit_package/<audit_id>/pages/rendered/<normalized-page>.json
```

## Render Plan Contract

Before any browser fallback executes, runtime may persist:

```text
audit_package/<audit_id>/render/render_plan.json
```

The render plan is a deterministic assessment artifact, not a rendered-page result. It must include:

1. `schema_version`
2. `audit_id`
3. `generated_at`
4. `summary.total_pages`
5. `summary.render_required_count`
6. `summary.plain_fetch_count`
7. `candidates[]` with `url`, `reason`, `wait_selectors`, and explainable `signals`

## Render Fallback Report

After bounded browser execution, runtime persists:

```text
audit_package/<audit_id>/render/render_fallback_report.json
```

This artifact records:

1. `max_rendered`
2. attempted, rendered, failed, and skipped counts
3. per-entry `status` (`rendered`, `failed`, `skipped_limit`)
4. optional render error text for failed entries

## Routing Policy

- Render if page classification or content type indicates JS-heavy behavior.
- Runtime may first emit render-required signals without executing browser fallback yet.
- The current executable browser path uses a bounded Playwright-based renderer behind the same `render.Result` contract.
- `http-refetch` may remain available only as a non-browser fallback tool, not as the primary JS-rendering strategy.
- Browser failures should not invalidate the whole audit run by default; extraction can continue on raw HTML while the failure is recorded in the fallback report.
- Keep a deterministic planner that can be explained and tested.
- Static HTML pages should continue through technical extraction without render dependency.

## Ownership

- `internal/render`: contracts and orchestration boundary.
- `internal/storage`: persistence of rendered artifacts.
- `scripts/render_page.mjs`: Playwright-based browser adapter invoked by runtime.

## Related Artifacts

- [Audit Lifecycle](/Users/vadimevgrafov/neurosearch-analyzer/docs/03-architecture/audit-lifecycle.md)
- [Repository Layout](/Users/vadimevgrafov/neurosearch-analyzer/docs/03-architecture/repository-layout.md)
- [render_plan.schema.json](/Users/vadimevgrafov/neurosearch-analyzer/schemas/render_plan.schema.json)
- [rendered_page.schema.json](/Users/vadimevgrafov/neurosearch-analyzer/schemas/rendered_page.schema.json)
