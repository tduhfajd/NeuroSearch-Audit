# Batch Runtime Verification

## Goal

Capture executable evidence that operators can run a bounded sequential batch manifest without inventing ad hoc scripts.

## Smoke Manifest

- Manifest: `testdata/fixtures/runtime/batch_manifest.sample.json`
- Output root: `/tmp/neurosearch-batch-smoke`

## Verification Steps

1. Execute batch runtime:

```bash
GOCACHE=/tmp/neurosearch-gocache go run ./cmd/runtime-batch \
  -manifest testdata/fixtures/runtime/batch_manifest.sample.json \
  -root /tmp/neurosearch-batch-smoke
```

2. Review batch report:

```bash
cat /tmp/neurosearch-batch-smoke/runtime_batches/batch_fixture_smoke/batch_report.json
```

3. Run regression baseline:

```bash
go test ./...
python3 scripts/validate_all.py
```

## Observed Evidence

- `runtime-batch` completed with `batch_id=batch_fixture_smoke`, `status=completed`, `items=2`
- persisted report path:

```text
/tmp/neurosearch-batch-smoke/runtime_batches/batch_fixture_smoke/batch_report.json
```

- both manifest items produced their own `audit_id`
- execution remained sequential and report-oriented rather than queue-based

## Interpretation

- operators now have a stable bounded batch entrypoint for repeated local runs;
- batch execution remains conservative and deterministic because it reuses the same single-run launcher and runtime policy;
- this is sufficient foundation for the next step: richer batch verification and phase closeout.
