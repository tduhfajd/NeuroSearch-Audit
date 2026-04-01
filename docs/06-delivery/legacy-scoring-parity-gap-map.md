# Legacy Scoring Parity Gap Map

## Short Answer

Current `neurosearch-analyzer` reports are already capable of producing client-facing `pdf/html/docx` bundles, but the **score methodology is not yet equivalent** to the legacy `NeuroSearch` MVP.

This is not a cosmetic discrepancy. The legacy system and the current system compute and interpret indices differently.

## Legacy NeuroSearch Methodology

Legacy NeuroSearch used:

- three integral indices:
  - `ai_readiness`
  - `generative_visibility`
  - `answer_fitness`
- weighted aggregation across methodological levels:
  - `L1_technical`
  - `L2_content`
  - `L3_semantic`
  - `L4_behavioral`
  - `L5_ai_interpretability`
- tier weighting:
  - `core`
  - `extended`
  - `experimental`
- missing-data normalization:
  - levels: `renormalize`
  - tiers: `ignore_unmeasured`

The authoritative source for that model lived in legacy `NeuroSearch/data/scoring/weights.yml`.

## Current neurosearch-analyzer Methodology

Current `neurosearch-analyzer` uses:

- five directional page scores:
  - `SEO`
  - `GEO`
  - `AEO`
  - `AIO`
  - `LEO`
- a simplified deterministic score builder:
  - base input = `coverage_score`
  - penalty input = accumulated contradiction severity
- a separate `lead_value_index` heuristic based on:
  - number of `P0` targets
  - number of `P1` targets
  - number of high contradictions
  - number of scored pages

This logic currently lives in `python/analysis/scoring.py`.

## Why They Are Not Equivalent

### 1. Different index families

Legacy:

- three integral indices representing audit-level readiness outcomes.

Current:

- five directional page-level projections plus one heuristic `lead_value_index`.

These are not direct renamings of the same measurement model.

### 2. Different scoring inputs

Legacy:

- factor assessments by methodological level and tier.

Current:

- mostly coverage and contradiction outputs.

The current system only recently started adding factual signals and still does not produce the legacy-style factor matrix.

### 3. Different aggregation rules

Legacy:

- weighted normalization over measured levels and tiers.

Current:

- direct page-score projection from coverage with simple contradiction penalties.

### 4. Different delivery semantics

Legacy reports discussed:

- three integral indices;
- five audit directions as explanatory lenses.

Current reports expose:

- five direct directional values and `lead_value_index`.

That means the same report layout can currently imply stronger methodology parity than the underlying scoring really supports.

## Practical Consequence

At the moment:

- the new report format can be made close to the legacy PDF;
- but the **numbers inside it should not yet be treated as legacy-equivalent indices**.

## Migration Rule

During parity migration:

1. `audit_package` remains the only analytical source of truth.
2. legacy scoring methodology is treated as a reference model, not as a source of old YAML runtime dependencies.
3. report parity and score parity must be tracked separately.

## Required Next Steps

1. Import the legacy scoring weights into the current repo as a stable reference artifact.
2. Define a current-to-legacy crosswalk:
   - which current outputs can feed `L1`-`L5`;
   - which legacy levels are still under-measured.
3. Introduce methodology metadata into report inputs so delivery documents do not over-claim parity before the score engine is aligned.
4. Replace or supplement the current score builder only after the crosswalk is explicit and testable.
