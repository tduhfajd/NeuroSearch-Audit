# Browser Rendering Operations

## Goal

Зафиксировать operational expectations для bounded browser fallback до появления более сложной browser orchestration layer.

## Current Limits

1. Runtime renders only URLs already selected by `render/render_plan.json`.
2. `ExtractStage.MaxRendered` bounds how many candidates are rendered in one run.
3. Browser execution uses an explicit timeout per page.
4. Rendered HTML larger than the configured limit is rejected.

## Failure Semantics

1. Browser render failure does not fail the whole audit run by default.
2. Failure is recorded in `render/render_fallback_report.json`.
3. Technical extraction falls back to raw HTML for failed render attempts.
4. Successfully rendered pages still flow through `pages/rendered/*` and `pages/technical/*` with `source=rendered`.

## Operator Checks

Review these files first:

1. `render/render_plan.json`
2. `render/render_fallback_report.json`
3. `pages/rendered/*.json`
4. `pages/technical/*.json`

## Deferred Operations

1. shared browser pool
2. screenshot capture
3. per-domain selector policies
4. browser-specific observability in `runtime-inspect`
