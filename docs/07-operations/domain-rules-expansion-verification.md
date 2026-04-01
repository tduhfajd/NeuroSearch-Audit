# Domain Rules Expansion Verification

## Goal

Capture live evidence that deeper commerce and service rules behave credibly across more than one real site shape.

## Live Verification Targets

### E-commerce Shape

- Site: `https://kuklapups.ru/`
- Run: `aud_20260312T142327Z_oyrmchi`
- Root: `/tmp/neurosearch-domain-rules-verify`

### Service Shape

- Site: `https://site-price.ru/`
- Run: `aud_20260312T142446Z_37s2yka`
- Root: `/tmp/neurosearch-domain-rules-verify-v2`

## Verification Steps

1. Execute live runtimes:

```bash
GOCACHE=/tmp/neurosearch-gocache go run ./cmd/runtime \
  -url https://kuklapups.ru/ \
  -max-depth 1 \
  -root /tmp/neurosearch-domain-rules-verify

GOCACHE=/tmp/neurosearch-gocache go run ./cmd/runtime \
  -url https://site-price.ru/ \
  -max-depth 1 \
  -root /tmp/neurosearch-domain-rules-verify-v2
```

2. Generate review artifacts:

```bash
python3 scripts/generate_review_artifacts.py \
  /tmp/neurosearch-domain-rules-verify/audit_package/aud_20260312T142327Z_oyrmchi

python3 scripts/generate_review_artifacts.py \
  /tmp/neurosearch-domain-rules-verify-v2/audit_package/aud_20260312T142446Z_37s2yka
```

3. Inspect runtime summaries:

```bash
GOCACHE=/tmp/neurosearch-gocache go run ./cmd/runtime-inspect \
  -root /tmp/neurosearch-domain-rules-verify \
  -audit-id aud_20260312T142327Z_oyrmchi \
  -attempt 1

GOCACHE=/tmp/neurosearch-gocache go run ./cmd/runtime-inspect \
  -root /tmp/neurosearch-domain-rules-verify-v2 \
  -audit-id aud_20260312T142446Z_37s2yka \
  -attempt 1
```

## Observed Evidence

### E-commerce Shape

- Runtime summary shows `32` fetched URLs, `31` HTML responses, and `30` persisted raw pages.
- `review_brief` surfaces deeper commerce-family gaps:
  - `product` focus area: `proof`, `terms`
  - `homepage` focus area: `proof`, `service_scope`
  - `wholesale` focus area: `process_steps`, `proof`
- priority pages remain business-relevant (`product`, `category`, `homepage`, `wholesale`, `contacts`, `delivery`, `return_policy`) rather than crawl noise.

### Service Shape

- Runtime summary shows `9` fetched URLs, `9` HTML responses, and `9` persisted raw pages after filtering `site.webmanifest`.
- `review_brief` classifies the run as `service` and keeps the main action on the homepage proof gap instead of inventing commerce-specific missing blocks.
- `contacts` remains fully covered and visible as an existing strength.

## Interpretation

- Deeper rules now separate commerce-heavy and service-oriented gaps more cleanly than the previous baseline.
- The service verification confirmed a useful crawler hardening follow-up: `.webmanifest` files are now filtered before analysis.
- The expanded domain rules are ready for calibration work on a broader benchmark set.
