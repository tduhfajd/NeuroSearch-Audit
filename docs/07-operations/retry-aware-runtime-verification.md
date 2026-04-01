# Retry-Aware Runtime Verification

## Goal

Capture executable evidence that runtime retries and operator-facing inspection expose transient stage failures clearly.

## Verification Steps

1. Run targeted retry tests:

```bash
go test ./internal/runtime -run 'TestRunnerRetriesRetryableStageError|TestInspectorReportsRetrySummary|TestInspectorReportsFailure' -v
```

2. Run full regression:

```bash
go test ./...
python3 scripts/validate_all.py
```

3. Generate synthetic retry inspection output:

```bash
go run ./cmd/runtime-inspect -root <synthetic-root> -audit-id aud_20260312T120000Z_retryop -attempt 1
```

## Expected Inspection Signals

- `metrics.retried_stages > 0`
- `metrics.total_retries > 0`
- `failure_summary.retryable_failures > 0`
- `failure_summary.buckets[]` shows the repeated `stage + code` pair
- stage-level output includes `attempt`, `max_attempts`, and `retry_count`

## Observed Evidence

Synthetic inspection output showed:

- `retried_stages = 1`
- `total_retries = 1`
- `failure_summary.buckets[0] = {stage: extracting, code: extract_run_error, count: 1}`
- `extracting` stage persisted as `attempt = 2`, `max_attempts = 2`, `retry_count = 1`

## Interpretation

- transient failures are now visible as first-class runtime signals, not only as final terminal failures;
- operators can distinguish retry noise from real terminal breakage without reading raw `run_state.json`;
- the runtime is ready for the next ops-hardening step: richer failure classes and batch-safe controls.
