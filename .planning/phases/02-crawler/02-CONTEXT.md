# Phase 2: Crawler - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

## Phase Boundary

Phase 2 delivers a working crawler pipeline that can start from a domain URL, crawl up to configured limits, collect page-level technical/semantic fields, validate robots/sitemap availability, support JS-rendered pages via Playwright, compute top pages by internal inlinks, and persist all collected data to PostgreSQL for downstream analyzer phases.

## Implementation Decisions

### Crawl orchestration strategy
- Use queue-based execution with RQ/Redis from Phase 2 start.
- `POST /audits` should enqueue crawl jobs instead of blocking request lifecycle.

### Crawl source strategy (sitemap + homepage)
- Use hybrid discovery: combine `sitemap.xml` URLs with homepage link expansion.
- Apply canonicalized URL deduplication before enqueueing crawl targets.

### Domain scope policy
- Default mode: strict host-only crawling.
- Add optional flag to include subdomains when explicitly enabled.

### Crawl limiting model
- Apply dual limits: max pages (`crawl_depth`) + max runtime timeout.
- Stop conditions should trigger graceful completion with partial persisted results.

### JS rendering policy
- Use heuristic hybrid mode for Playwright activation.
- Primary parse via HTTP; escalate to Playwright when SPA/empty-content signals are detected.

### Link/inlinks data model
- Store internal and external links as separate extracted sets.
- Calculate `inlinks_count` from internal graph only.

### robots/sitemap behavior
- Enforce strict robots compliance by default.
- Provide explicit override switch for audit mode when disallowed pages must still be inspected.

### PageSpeed integration
- Implement provider abstraction.
- Primary provider: Google PageSpeed API; fallback provider: local Lighthouse CLI.

### Crawl error capture
- Persist detailed crawl error entries inside `audits.meta["crawl_errors"]`.
- Avoid schema expansion in Phase 2 (no new DB table for crawl events).

### Persistence strategy
- Use batched writes.
- Use idempotent upsert semantics keyed by (`audit_id`, `url`).

### Concurrency model
- Support configurable concurrency with safe defaults.
- Keep conservative default tuned for local Mac runtime stability.

### Retry policy
- Retry transient failures up to 2 times.
- Use short exponential backoff for network/temporary upstream errors.

### Claude's Discretion
- Exact heuristic thresholds for Playwright escalation (empty-text cutoff, script-density signals, etc.).
- Concrete default values for timeout, batch size, concurrency, and backoff intervals.
- Internal module boundaries (`spider.py` vs `playwright_utils.py` responsibilities) if behavior remains aligned with agreed decisions.
- Shape and granularity of `crawl_errors` records inside `audits.meta` as long as they are diagnosable.

## Specific Ideas

- Build crawler around resilient local execution first: predictable completion is prioritized over maximal throughput.
- Keep Phase 2 storage format directly consumable by Phase 3 analyzer (clean internal-link graph + normalized per-page fields).
- Preserve strict defaults (host scope + robots respect) while exposing explicit opt-in overrides for power use cases.
- Use provider abstraction early for PageSpeed to avoid rework when API key is unavailable.

## Deferred Ideas

- Dedicated `crawl_events` table for high-volume telemetry (deferred to future hardening/scaling phase).
- Advanced URL canonicalization across cross-domain canonicals and language alternates (deferred).
- Distributed crawl workers or multi-audit parallel orchestration (deferred beyond current local single-user scope).
- Full runtime observability dashboards/metrics for crawler internals (deferred to later polish/ops work).

---

*Phase: 02-crawler*
*Context gathered: 2026-02-26*
