# Legacy NeuroSearch Migration Map

## Decision

The legacy `/Users/vadimevgrafov/NeuroSearch` project is reused as a **delivery/reporting reference**, not as the analytical source of truth for the current system.

The current `neurosearch-analyzer` remains authoritative for:

- crawl and runtime execution
- technical extraction
- semantic blocks
- entities and normalized facts
- coverage, contradictions, scores, recommendations
- package validation and approval

## Reuse As-Is Or Near-As-Is

These legacy assets are strong enough to migrate with limited adaptation:

1. report structure and editorial framing
   - concise executive summary
   - "what was evaluated"
   - interpreted score sections
   - strengths, risks, priorities, roadmap

2. branded report-generation layer
   - PDF / HTML / DOCX rendering flow
   - Quarto / LaTeX templates
   - visual assets and brand config

3. methodology taxonomy as input material
   - factors
   - surfaces
   - core sets
   - scoring heuristics

## Reuse With Rewrite

These legacy pieces are useful conceptually but must not be ported literally:

1. factor-assessment flows
   - old `factor_assessments.yml` is too sparse and collector-dependent
   - the current system should derive reporting inputs from package artifacts instead

2. report assembly inputs
   - old `report.yml` / `proposal.yml` are replaced by package-derived JSON projections
   - migration should produce new adapter artifacts, not recreate old YAML contracts

3. score presentation
   - old report framing is reusable
   - current package metrics and rules remain authoritative

## Do Not Reuse

These legacy parts should stay out of the new core:

1. markdown-to-json back-parsing
   - parsing generated markdown back into structured state is brittle

2. sparse collector assumptions
   - old reporting often compensated for missing evidence with inferred narrative

3. legacy audit as the primary package model
   - the new `audit_package` already provides a better deterministic contract

## Migration Sequence

1. Create `exports/client_report_input.json` from approved package artifacts.
2. Port legacy report templates to consume `client_report_input.json`.
3. Rebuild PDF / HTML / DOCX generation on the new adapter.
4. Migrate stronger expert-report and commercial-offer style documents only after report generation is stable.

## First Bridge Artifact

`exports/client_report_input.json` is the canonical migration bridge.

It should:

- be deterministic
- derive only from approved package artifacts
- carry client-facing narrative structure without inventing new facts
- become the only supported input for the migrated legacy report layer
