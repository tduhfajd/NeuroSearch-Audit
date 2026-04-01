# Benchmark Workflow

## Goal

Держать calibration changes привязанными к reproducible fixtures, а не к единичным pilot впечатлениям.

## Benchmark Set

Текущий benchmark набор включает:

1. reproducibility pair in `testdata/fixtures/reproducibility/`
2. benchmark cases in `testdata/fixtures/benchmark/`
3. package-adjacent delivery evidence from `testdata/package-sample/handoff/`
4. live-review snapshots from real service and commerce runs

## What A Benchmark Case Must Express

Каждый benchmark case должен фиксировать:

1. `segment`
2. `page_type`
3. `source_fixture`
4. expected delivery or calibration signals
5. notes explaining why the case matters

## Validation Path

```text
python3 scripts/validate_benchmark_set.py
python3 scripts/validate_reproducibility.py testdata/fixtures/reproducibility/run_a.json testdata/fixtures/reproducibility/run_b.json
python3 scripts/diff_benchmark_cases.py <before_benchmark_dir> <after_benchmark_dir>
```

## Calibration Rule

- benchmark set must include more than one workflow shape before policy changes are proposed;
- benchmark set should cover service, content, and commercial evidence before stronger policy changes are proposed;
- service-page pilot evidence cannot automatically generalize to content workflows;
- friction signals can justify integration investigation, but not direct scoring changes by themselves.

## Review Use

Read this together with:

- [delivery-friction-rubric.md](/Users/vadimevgrafov/neurosearch-analyzer/docs/06-delivery/delivery-friction-rubric.md)
- [scale-out-criteria.md](/Users/vadimevgrafov/neurosearch-analyzer/docs/06-delivery/scale-out-criteria.md)
- [calibration-decisions.md](/Users/vadimevgrafov/neurosearch-analyzer/docs/06-delivery/calibration-decisions.md)
