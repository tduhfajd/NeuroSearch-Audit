# Runtime Retention Policy

## Goal

Bound runtime leftovers so repeated local and pilot usage does not accumulate stale `runtime/` and `runtime_batches/` directories indefinitely.

## Safety Boundary

Cleanup is intentionally conservative:

1. `audit_package/` is never deleted by the cleanup script
2. only `runtime/` attempt directories are eligible
3. only `runtime_batches/` batch-report directories are eligible
4. dry-run is the default mode

## Cleanup Command

```bash
python3 scripts/cleanup_runtime.py <output_root> --retention-days 7
```

Apply mode:

```bash
python3 scripts/cleanup_runtime.py <output_root> --retention-days 7 --apply
```

## Default Retention Guidance

- local smoke roots: `7` days
- pilot workspaces: `14` days if operators still review recent runtime state manually
- long-term source of truth remains `audit_package/`, not runtime leftovers

## Expected Output

The command prints a JSON summary with:

1. `candidates[]`
2. `deleted[]`
3. retention window
4. target root

## Why This Exists

- `runtime/` is mutable execution state and grows with repeated attempts
- `runtime_batches/` is operational convenience, not the approved package surface
- stale runtime leftovers should not be allowed to masquerade as current operational state
