# Runet Rules Verification

## Goal

Capture live evidence that Runet-specific trust, payment, legal, and messenger rules improve audit usefulness on a real RU site.

## Live Verification Target

- Site: `https://kuklapups.ru/`
- Run: `aud_20260312T110907Z_yvqlfua`
- Root: `/tmp/neurosearch-kuklapups-runet-v2`

## Verification Steps

1. Execute live runtime:

```bash
GOCACHE=/tmp/neurosearch-gocache go run ./cmd/runtime \
  -url https://kuklapups.ru/ \
  -max-depth 1 \
  -root /tmp/neurosearch-kuklapups-runet-v2
```

2. Generate review artifacts:

```bash
python3 scripts/generate_review_artifacts.py \
  /tmp/neurosearch-kuklapups-runet-v2/audit_package/aud_20260312T110907Z_yvqlfua
```

3. Inspect runtime:

```bash
GOCACHE=/tmp/neurosearch-gocache go run ./cmd/runtime-inspect \
  -root /tmp/neurosearch-kuklapups-runet-v2 \
  -audit-id aud_20260312T110907Z_yvqlfua \
  -attempt 1
```

## Observed Evidence

- Crawl discovered `32` fetched URLs with `31` HTML responses and `30` raw pages persisted.
- Semantic output produced focused Runet-oriented blocks instead of site-wide positives:
  - `contacts`: `7`
  - `messengers`: `7`
  - `legal_trust`: `7`
  - `payment_options`: `22`
- The focused pages included `homepage`, `contacts`, `delivery`, `return_policy`, `wholesale`, and commerce pages rather than all crawled pages.
- Review output now surfaces:
  - `contacts` page with `coverage_score=1.0`
  - `delivery` pages with `coverage_score=1.0`
  - `return_policy` pages with `coverage_score=1.0`
  - `wholesale` page with remaining gaps narrowed to `process_steps` and `proof`

## Interpretation

- RU trust/legal/payment signals are now influencing downstream page blocks and coverage, not just sitting in technical artifacts.
- The current ruleset is meaningfully better than URL/title-only heuristics for RU commerce/service sites.
- Remaining gaps are still mostly content-quality gaps (`proof`, `process_steps`, some `terms`), not missing trust-signal detection.
