# Runtime Observability

## Goal

Дать оператору быстрый способ понять, что происходит с audit run, не открывая вручную `run_state.json` и не исследуя package files по каталогам.

## Inspection Surface

Первый inspection path для MVP-2:

```text
go run ./cmd/runtime-inspect -root <output_root> -audit-id <audit_id> -attempt <n>
```

Команда читает persisted `runtime/<audit_id>/attempts/<nnn>/run_state.json` и выводит compact summary:

1. `status`
2. `current_stage`
3. `last_error`
4. `metrics`
5. `failure_summary`
6. `crawl_quality`
7. `stages[]` with per-stage duration and status

Aggregate inspection path for repeated runs:

```text
go run ./cmd/runtime-summary -root <output_root>
```

Эта команда читает все `runtime/*/attempts/*/run_state.json` и `runtime_batches/*/batch_report.json`, чтобы дать root-level ops summary.

## Baseline Metrics

Пока фиксируются только coarse metrics, достаточные для pilot reviews:

1. `total_duration_ms`
2. `current_stage_duration_ms`
3. `completed_stages`
4. `failed_stages`
5. `pending_stages`
6. `retried_stages`
7. `total_retries`
8. `last_updated_at`
9. `run_started_at`
10. `run_finished_at`

## Failure Summary

Если run уже сталкивался с transient retries или terminal failures, inspection выводит `failure_summary`:

1. `retryable_failures`
2. `terminal_failures`
3. `buckets[]` with `stage`, `code`, `count`

Это позволяет быстро понять:

- какие stage codes повторяются;
- где transient issues доминируют над terminal failures;
- стоит ли смотреть retry policy или deeper runtime bug.

## Crawl Quality

Если crawl artifacts уже persisted, inspection дополнительно выводит `crawl_quality`:

1. `visited_url_count`
2. `skipped_url_count`
3. `filtered_url_count`
4. `fetch_failure_count`
5. `fetched_count`
6. `html_count`
7. `non_html_count`
8. `raw_page_count`
9. `submitted_count`
10. `sitemap_count`
11. `discovered_count`
12. `discovery_mode`
13. `min_request_interval_ms`
14. `max_inflight_per_host`
15. `warnings[]`

Это позволяет быстро увидеть, не доминируют ли в run utility URLs, non-HTML targets или слишком агрессивная фильтрация.
И также понять, под какой crawl-throttling policy шел live run.

Для frontier review оператору также полезно смотреть `crawl/fetch_log.json`:

1. `source=submitted` показывает исходный URL запуска;
2. `source=sitemap` показывает URLs, попавшие в frontier через `robots.txt`/sitemap discovery;
3. `source=discovered` показывает URLs, найденные уже во время обхода страниц.

## Why This Is Enough For MVP-2

- помогает видеть hung/slow stage без UI;
- дает основу для p50/p95 pipeline duration из pilot batch;
- не требует отдельного metrics backend раньше времени;
- совместимо с будущим HTTP/API layer, потому что опирается на stable inspection projection, а не на console-only формат.

## Operational Rules

- Inspection читает только persisted runtime state и ничего не мутирует.
- Runtime metrics считаются derived view поверх stage timestamps.
- Retry/failure summaries считаются derived view поверх stage retry history and terminal stage state.
- `crawl_quality` считается derived view поверх `crawl/visited_urls.json`, `crawl/fetch_log.json` и `pages/raw/`.
- Seed-source review остается в `crawl/fetch_log.json`, а не в `run_state.json`, чтобы execution state не дублировал crawl artifacts.
- Любой новый observability sink должен сохранять эквивалент этих baseline numbers.
- Retention and cleanup of stale runtime state is handled separately; see [runtime-retention-policy.md](/Users/vadimevgrafov/neurosearch-analyzer/docs/07-operations/runtime-retention-policy.md).

## Review Link

При pilot review сопоставляйте эти метрики с criteria из [scale-out-criteria.md](/Users/vadimevgrafov/neurosearch-analyzer/docs/06-delivery/scale-out-criteria.md), особенно:

- `p50/p95 pipeline duration`
- queue backlog growth
- render-required page ratio
- repeated operator complaints linked to a specific boundary
