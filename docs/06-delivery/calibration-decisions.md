# Calibration Decisions

## Goal

Зафиксировать calibration decisions так, чтобы Phase 09 не превращалась в неявный rule tweaking.

## Decision 2026-03-11-01

- Status: accepted
- Scope: pilot calibration baseline
- Evidence:
  - `testdata/package-sample/handoff/aud_20260311T120000Z_abc1234/delivery_friction_report.json`
  - `testdata/fixtures/benchmark/service_priority_case.json`
  - `testdata/fixtures/benchmark/content_light_case.json`

### Observed Signals

- service workflow shows `manual_tax_level=medium`
- reformatting tax is `medium`
- CRM signal is `weak`
- task tracker signal is `strong`
- direct handoff signal is `weak`

### Decision

1. Do not change contradiction severity or score formulas based only on delivery friction.
2. Keep file-based exports as the default MVP-2 mechanism.
3. Treat task-tracker integration as the first integration candidate to evaluate in `09-02`.
4. Do not promote CRM integration yet because the current signal is only `weak`.

### Why

- The observed pain is operational transfer friction, not evidence that analysis severity is wrong.
- A single service-heavy pilot case is insufficient to generalize scoring or severity changes.
- The strongest repeated signal currently points to backlog transfer, not commercial metadata sync.

### Deferred Until More Evidence

- direct CRM write
- severity retuning for contradictions
- any broad change to LVI or score weighting

## Diff Workflow

When benchmark expectations change, compare the previous and current benchmark directories explicitly:

```bash
python3 scripts/diff_benchmark_cases.py <before_benchmark_dir> <after_benchmark_dir>
```

The diff must be reviewed before updating this decision log so calibration changes stay explainable.

## Decision 2026-03-11-02

- Status: accepted
- Scope: first integration candidate selection
- Evidence:
  - `testdata/package-sample/handoff/aud_20260311T120000Z_abc1234/delivery_friction_report.json`
  - `docs/03-architecture/integration-points.md`

### Decision

1. Select task tracker write integration as the first direct integration candidate.
2. Keep CRM and direct AI handoff as deferred candidates.
3. Limit the candidate to one-way task creation from `exports/backlog.json`.

### Why

- strongest measured signal points to tracker-specific field mapping pain
- current export model already gives a stable backlog bridge
- this is a narrower and safer pilot step than CRM or two-way sync
