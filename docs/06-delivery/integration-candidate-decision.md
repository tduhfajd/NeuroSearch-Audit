# Integration Candidate Decision

## Goal

Зафиксировать, какая интеграция становится первой кандидатной после MVP-2 и почему более широкие варианты пока откладываются.

## Selected Candidate

- Candidate: task tracker write integration
- Status: selected for specification, not yet approved for implementation

## Evidence Used

1. `testdata/package-sample/handoff/aud_20260311T120000Z_abc1234/delivery_friction_report.json`
2. `docs/06-delivery/calibration-decisions.md`
3. `docs/03-architecture/integration-points.md`

## Why This Candidate Wins

- strongest current signal is `task_tracker_signal=strong`
- operator complaint explicitly mentions tracker-specific field mapping
- `exports/backlog.json` already provides a stable bridge artifact
- implementation envelope can stay narrow and one-way

## Why The Other Candidates Lose For Now

### CRM Direct Write

- signal is only `weak`
- missing export `crm_summary` is real, but current evidence is not strong enough for live write complexity
- commercial field mapping is more variable across pilot users

### Direct AI Handoff Integration

- direct handoff signal is only `weak`
- current package + prompt workflow is operationally acceptable
- logging and checklist path already reduce ambiguity without API coupling

## Approval Conditions Before Implementation

1. at least one target tracker is chosen explicitly
2. required field mapping is fixed and documented
3. dry-run and failure logging are part of the implementation envelope
4. package remains the source of truth

## Rejected Misreadings

- This is not approval to implement every tracker integration.
- This is not approval for two-way sync.
- This does not justify score or severity retuning.
