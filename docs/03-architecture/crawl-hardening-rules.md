# Crawl Hardening Rules

## Goal

Зафиксировать deterministic rules, которые делают live crawl пригодным для повторяемых real-site аудитов без засорения extract/analyze path.

## Current Rule Set

### URL-level filtering

By default the crawler rejects:

1. asset extensions such as `css`, `js`, `ico`, images, fonts, archives, media, and `pdf`;
2. utility paths such as `/cart`, `/login`, `/signup`, `/order`, `/search`, `/forgotpassword`;
3. query variants with `quickview`.

These rules are applied before links expand the crawl frontier.

### Content-type gating

Raw page artifacts are persisted only for HTML-like responses:

1. `text/html`
2. `application/xhtml+xml`
3. empty content type as a conservative fallback

Non-HTML fetches may remain visible in `crawl/fetch_log.json`, but they do not become `pages/raw/*` or `pages/technical/*`.

### Frontier discovery

The runtime no longer seeds the crawl frontier from the submitted URL alone:

1. the submitted URL is always enqueued as `source=submitted`;
2. `robots.txt` is fetched opportunistically to discover `Sitemap:` hints;
3. sitemap entries are bounded and filtered through the same deterministic crawl policy before they enter the queue as `source=sitemap`;
4. links found during page fetch continue to enter as `source=discovered`.

This keeps discovery auditable without turning the runtime into a general-purpose crawler.

### Domain throttling

Live runtime uses explicit bounded crawl policy defaults:

1. `min_request_interval_ms = 250`
2. `max_inflight_per_host = 1`

Interpretation:

- repeated requests to the same host are spaced by at least `250ms`;
- current runtime keeps same-host crawling single-flight by design;
- this is intentionally conservative until a richer batch/concurrency layer exists.

## Why This Rule Set Exists

- E-commerce sites expose many utility and asset links in navigation and templates.
- If these URLs enter extraction, analysis quality degrades faster than coverage improves.
- The deterministic core should prefer a smaller, cleaner page set over noisy breadth.

## Tradeoffs

- Some valid but unusual URLs can be filtered out too aggressively.
- Search or auth-adjacent business pages are intentionally out of scope for the default audit surface.
- RSS and other non-HTML endpoints may still appear in fetch logs when they pass URL filters but fail the HTML gate.

## Deferred Improvements

1. full robots.txt compliance beyond sitemap discovery
2. crawl-delay scheduling
3. canonical clustering
4. JS-render fallback for pages that remain thin under plain HTTP fetch
5. configurable per-domain crawl policy overrides
6. adaptive throttling driven by host behavior or robots hints
