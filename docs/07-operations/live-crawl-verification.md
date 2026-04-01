# Live Crawl Verification

## Goal

Сохранить проверяемое evidence, что crawler hardening улучшил live audit output на реальном сайте, а не только в unit tests.

## Verification Site

- Domain: `https://kuklapups.ru/`
- Crawl depth: `1`

## Compared Runs

### Baseline live run

- Audit ID: `aud_20260311T194151Z_nsg76ji`
- Output root: `/tmp/neurosearch-kuklapups-live`
- Result: noisy package with `45` raw pages

Noise examples:

- `quickview` product variants
- `cart`, `login`, `signup`, `search`
- `favicon.ico`
- CSS asset URLs

### Hardened run

- Audit ID: `aud_20260311T195114Z_w7puldy`
- Output root: `/tmp/neurosearch-kuklapups-hardened`
- Result: cleaned package with `18` raw pages

### Observability run

- Audit ID: `aud_20260312T065855Z_5eny7uq`
- Output root: `/tmp/neurosearch-kuklapups-observed-v2`
- Result: same cleaned package shape plus explicit crawl-quality counters

Observed counters:

1. `visited_url_count=19`
2. `filtered_url_count=26`
3. `html_count=18`
4. `non_html_count=1`
5. `raw_page_count=18`

### Seeded discovery run

- Audit ID: `aud_20260312T074901Z_hlcuy6y`
- Output root: `/tmp/neurosearch-kuklapups-seeded`
- Result: sitemap-aware frontier expansion with `32` fetched URLs and explicit discovery-source counters

Observed counters:

1. `submitted_count=1`
2. `sitemap_count=19`
3. `discovered_count=12`
4. `discovery_mode=mixed`
5. `raw_page_count=30`

Compared with the observability baseline, the seeded run added `13` fetched URLs, including:

- `/dostavka/`
- `/optovikam/`
- `/video-obzory/`
- several `video-obzory/*` content pages
- additional category and product-detail pages surfaced from sitemap discovery

## Acceptance Outcome

- Asset and utility noise no longer dominates the extractable page set.
- Non-HTML content still appears in fetch logs when relevant, but no longer enters extraction.
- Operators and reviewers now get crawl-quality warnings without opening low-level artifacts by hand.
- Sitemap-aware seeding expands the crawl frontier beyond homepage links on a real site without removing the existing noise filters.

## Remaining Gaps

1. RSS still appears in fetch logs and may merit a stricter URL-level filter if it repeatedly adds no value.
2. Only sitemap discovery is implemented from `robots.txt`; full robots compliance and crawl-delay handling remain deferred.
3. No JS-render fallback for client-rendered sites.
