# Runtime Summary Verification

## Goal

Capture executable evidence that operators can view aggregate runtime and batch health across a whole output root.

## Summary Command

```bash
GOCACHE=/tmp/neurosearch-gocache go run ./cmd/runtime-summary -root /tmp/neurosearch-batch-smoke
```

## Expected Signals

1. total run count
2. completed/failed/running/pending run counts
3. total retries
4. grouped failure buckets
5. recent batch summaries

## Why This Matters

- repeated pilot usage should not require opening one `run_state.json` per audit
- ops review should be able to spot retry and failure patterns across recent runs
- batch-level health should be visible in the same aggregate surface
