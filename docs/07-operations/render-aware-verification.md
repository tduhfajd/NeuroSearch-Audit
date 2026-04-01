# Render-Aware Verification

## Goal

Зафиксировать проверяемое evidence, что runtime различает plain-fetch и render-required страницы и умеет запускать bounded browser fallback.

## Verification Inputs

### Dynamic fixture sample

- URL: `https://example.com/app`
- Mode: `fixture-mode`
- Output root: `/tmp/neurosearch-render-fixture-run`
- Audit ID: `aud_20260312T085442Z_l2wkijq`

Observed artifacts:

1. `render/render_plan.json` reports `total_pages=1`, `render_required_count=1`, `plain_fetch_count=0`
2. candidate reason is `spa-url-pattern`
3. `render/render_fallback_report.json` records one attempted and one rendered fallback
4. `pages/rendered/example.com_app.json` exists with `render_mode=playwright-browser`
5. `pages/technical/example.com_app.json` uses `source=rendered`

### Live site control sample

- URL: `https://kuklapups.ru/`
- Mode: live runtime
- Output root: `/tmp/neurosearch-kuklapups-render-aware`
- Audit ID: `aud_20260312T085055Z_oz5xp2i`

Observed artifacts:

1. `render/render_plan.json` reports `total_pages=30`, `render_required_count=0`, `plain_fetch_count=30`
2. no rendered-page artifacts are emitted
3. live runtime remains package-complete and continues through the plain-fetch path

## Acceptance Outcome

- The runtime now emits deterministic render-required signals and can execute a real browser fallback for flagged pages.
- Bounded fallback execution remains limited and auditable through `render_fallback_report.json`.
- Plain-fetch pages do not get promoted into rendered artifacts implicitly.

## Remaining Gaps

1. Render-required heuristics are still conservative and may miss JS-heavy pages with rich server-rendered shells.
2. Review and observability layers do not yet surface render-plan/fallback counters directly.
3. Browser pool management and per-domain wait overrides remain deferred.
