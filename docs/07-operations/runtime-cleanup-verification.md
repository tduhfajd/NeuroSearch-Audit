# Runtime Cleanup Verification

## Goal

Capture executable evidence that runtime cleanup removes stale mutable leftovers without touching `audit_package/`.

## Verification Steps

1. Run targeted cleanup test:

```bash
python3 -m pytest scripts/test_cleanup_runtime.py
```

2. Run script compile and validation baseline:

```bash
python3 -m compileall scripts
python3 scripts/validate_all.py
```

3. Run cleanup smoke on a temporary root:

```bash
python3 scripts/cleanup_runtime.py <temp-root> --retention-days 7
python3 scripts/cleanup_runtime.py <temp-root> --retention-days 7 --apply
```

## Observed Evidence

The cleanup smoke removed:

- `runtime/aud_old/attempts/001`
- `runtime_batches/batch_old`

And preserved:

- fresh runtime attempt directories
- `audit_package/aud_old`

## Interpretation

- cleanup is now bounded to mutable runtime leftovers;
- approved and package-shaped audit outputs remain outside the deletion surface;
- this gives operators a safe maintenance path before aggregate ops summaries are added.
