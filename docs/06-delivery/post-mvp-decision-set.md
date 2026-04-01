# Post-MVP Decision Set

## Goal

Зафиксировать итоговые go/no-go решения после завершения `MVP-2 Pilot Runtime And Delivery`.

## Go Decisions

### GO-001 Task Tracker Write Integration

- Decision: go for a narrowly scoped post-MVP implementation candidate
- Reason:
  - strongest measured signal is `task_tracker_signal=strong`
  - `exports/backlog.json` already provides a stable bridge
  - scope can remain one-way and package-derived

Guardrails:

1. one target tracker at a time
2. dry-run mode required
3. no two-way sync
4. package remains source of truth

## No-Go Decisions

### NO-GO-001 CRM Direct Write

- Decision: no-go for the next milestone by default
- Reason:
  - current CRM signal is only `weak`
  - missing `crm_summary` alone is not enough to justify live-write complexity

### NO-GO-002 Severity / Score Retuning From Delivery Friction

- Decision: no-go
- Reason:
  - delivery friction is operational evidence, not proof that severity or scoring rules are wrong

### NO-GO-003 Two-Way Downstream Sync

- Decision: no-go
- Reason:
  - it would blur deterministic-core boundaries and has no current pilot justification

## Deferred Decisions

### DEFER-001 Dedicated Broker Upgrade

- Keep deferred until queue backlog and delivery guarantees show repeated pressure per [scale-out-criteria.md](/Users/vadimevgrafov/neurosearch-analyzer/docs/06-delivery/scale-out-criteria.md)

### DEFER-002 ClickHouse / Heavy Analytics Store

- Keep deferred until repeated cross-audit analytical questions become a proven bottleneck

### DEFER-003 Dedicated Render Pool Hardening

- Keep deferred until render-heavy usage materially affects throughput or stability

### DEFER-004 Direct AI Handoff Integration

- Keep deferred until the current package + prompt + checklist workflow shows repeated manual bundling pain stronger than `weak`

## Milestone Closeout Position

After `MVP-2`, the project is ready to:

1. keep running pilots on the current deterministic core;
2. implement one narrow task-tracker integration if the next milestone is integration-focused;
3. continue deferring broader scale work unless new benchmark evidence crosses explicit thresholds.
