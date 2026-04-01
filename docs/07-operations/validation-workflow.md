# Validation Workflow

## Goal

Сделать quality gates исполнимыми: для каждого gate определить проверку, входы, owner module и ожидаемый способ запуска.

## Gate To Validator Mapping

| Gate | Enforced By | Inputs | Primary Owner | Phase Target |
|---|---|---|---|---|
| `G-001 Crawl Completeness Gate` | crawl completeness validator | `audit.json`, `crawl/visited_urls.json`, `crawl/link_graph.json` | M-03 Crawler | Phase 02 |
| `G-002 Data Contract Gate` | schema validation runner | all JSON artifacts + `schemas/*.json` | M-13 Package Builder | Phase 05 |
| `G-003 Evidence Coverage Gate` | evidence coverage validator | findings, recommendations, prompts, source references | M-14 Evidence Validator | Phase 05 |
| `G-004 Contradiction Integrity Gate` | contradiction validator | `contradictions.json`, normalized facts, source URLs | M-09 Contradiction Engine | Phase 04 |
| `G-005 Scoring Reproducibility Gate` | reproducibility runner | frozen analysis artifacts + scoring output | M-10 Scoring Engine | Phase 04 |
| `G-006 Prompt Compliance Gate` | prompt compliance validator | `prompts/*.md`, manifest, required sections policy | M-12 Prompt Generator | Phase 05 |
| `G-007 Final Package Gate` | package assembly validator | `manifest.json`, package file inventory, stage statuses | M-13 Package Builder | Phase 05 |

## Validation Layers

### Layer 1: Local Plan Validation

Used during active plan execution.

- check touched files exist and are substantive;
- run language-specific tests where code exists;
- confirm plan `must_haves` are satisfied;
- update plan summary with residual risks.

### Layer 2: Phase Verification

Used before marking a phase complete.

- review `Observable Truths`;
- confirm expected artifacts are real and wired;
- execute available automated checks;
- perform goal-backward review from roadmap success criteria.

### Layer 3: Package Validation

Used once end-to-end pipeline exists.

- validate JSON artifacts against schemas;
- re-generate derived exports separately from package approval so stale outputs cannot block their own refresh;
- validate evidence links and contradiction source counts;
- validate prompt structure and no-fabrication rules;
- validate manifest completeness and status consistency.

## Expected Validation Commands

These commands are placeholders for the future repository implementation:

```text
python3 scripts/validate_contracts.py <audit_package_path>
python3 scripts/validate_evidence.py <audit_package_path>
python3 scripts/validate_prompts.py <audit_package_path>
python3 scripts/validate_reproducibility.py <baseline.json> <candidate.json>
go test ./...
pytest
```

## Failure Policy

- Contract violations block package approval.
- Missing evidence on high/medium findings blocks package approval.
- Reproducibility failures block publication of scores.
- Incomplete automated checks are allowed only in documentation-heavy phases and must be called out explicitly in phase summaries.

## Documentation-Only Phase Rule

For phases that mostly create contracts and docs:

- verification may be structural and manual;
- missing automated checks must be listed as a temporary gap;
- every new contract must identify its future validator or enforcement point.

## Ownership Notes

- Schema validation should stay centralized even if schemas are produced by different modules.
- Evidence validation should remain independent from the recommendation generator so it can reject unsupported claims.
- Reproducibility checks should compare normalized outputs while ignoring permitted timestamp fields.
