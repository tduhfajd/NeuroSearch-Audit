# Domain Throttling Verification

## Goal

Capture executable evidence that live crawl execution now carries explicit domain-throttling defaults and persists them in crawl artifacts.

## Verification Steps

1. Run targeted crawl/runtime/storage tests:

```bash
go test ./internal/crawl ./internal/runtime ./internal/storage -v
```

2. Run package validation:

```bash
python3 scripts/validate_all.py
```

## Expected Evidence

- `crawl/visited_urls.json` contains `throttle_policy`
- `throttle_policy.min_request_interval_ms = 250`
- `throttle_policy.max_inflight_per_host = 1`
- runtime inspection exposes the same fields through `crawl_quality`

## Observed Evidence

- `TestWorkerRunAppliesThrottleBetweenSameHostRequests` confirmed a `250ms` wait between two same-host requests.
- `TestInspectorIncludesCrawlQuality` confirmed that `runtime-inspect` surfaces:
  - `min_request_interval_ms = 250`
  - `max_inflight_per_host = 1`

## Interpretation

- live runtime now has an explicit conservative crawl-throttling policy rather than an implicit single-threaded implementation detail;
- operators can inspect the crawl policy used for a run without opening low-level code or guessing from behavior.
