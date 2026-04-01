# Task Tracker Integration Candidate

## Goal

Определить первый direct integration candidate для MVP-2 follow-through без преждевременной реализации и без размывания границ deterministic core.

## Decision

Первый кандидат: `Task Tracker Write Integration`

Причина выбора:

- strongest current signal = `task_tracker_signal=strong`
- repeated pain связана с ручным переносом backlog items
- candidate опирается на уже существующий `exports/backlog.json`

Не выбранные варианты на этом этапе:

- CRM direct write
- direct AI orchestration integration
- two-way sync between package and downstream systems

## Scope

Интеграция должна делать только одно:

- создавать downstream task items из `exports/backlog.json`

Что не входит:

- редактирование package
- обновление audit state из task tracker
- чтение чужих полей обратно в deterministic core
- создание эпиков, досок, проектов, sprint planning logic

## Source Of Truth

Source of truth остается:

1. `audit_package/<audit_id>/analysis/recommendations.json`
2. `exports/backlog.json`

Integration payload only derives from those artifacts.

## Minimal Payload Mapping

Каждый downstream task должен map'иться из одного `items[]` entry в `exports/backlog.json`:

1. `audit_id` -> custom field or label
2. `recommendation_id` -> external id / dedupe key
3. `priority` -> priority field
4. `expected_impact` -> issue summary or description section
5. `acceptance_criteria[]` -> checklist/body section
6. `related_findings[]` -> evidence references section

## Auth Assumptions

- pilot-safe token scoped only to create issues/tasks
- no broad admin permissions
- auth material stored outside package artifacts

## Rollout Limits

Первая реализация, если будет одобрена, должна быть ограничена:

1. one-way write only
2. one target tracker at a time
3. explicit dry-run mode
4. explicit mapping config checked into repo docs/config, not hidden in prompts
5. no mutation of already created tasks unless a later phase approves idempotent update behavior

## Failure Model

- export remains usable even if integration fails
- failed write does not change package approval status
- integration logs must reference `audit_id` and `recommendation_id`

## Why Not CRM First

- current CRM signal is only `weak`
- observed missing export is `crm_summary`, but repeated operational pain is stronger in task decomposition and tracker-specific field mapping
- CRM write would require less-stable commercial field assumptions than the current backlog transfer candidate

## Traceability

- [integration-points.md](/Users/vadimevgrafov/neurosearch-analyzer/docs/03-architecture/integration-points.md)
- [export-boundaries.md](/Users/vadimevgrafov/neurosearch-analyzer/docs/03-architecture/export-boundaries.md)
- [calibration-decisions.md](/Users/vadimevgrafov/neurosearch-analyzer/docs/06-delivery/calibration-decisions.md)
