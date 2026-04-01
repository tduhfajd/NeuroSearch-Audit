# Delivery Friction Rubric

## Goal

Измерять остаточную ручную работу после package approval так, чтобы решения о live integrations принимались по повторяемым operational signals, а не по вкусу команды.

## Measurement Scope

Рубрика применяется после:

1. package approval;
2. generation of `exports/review_brief.*`;
3. generation of `exports/backlog.json`;
4. initial external AI handoff or review preparation.

## Core Metrics

### Manual Steps

Считать каждый отдельный операторский шаг, который нельзя выполнить простым открытием готового artifact:

- копирование данных между системами;
- ручной выбор нужного export;
- ручная фиксация handoff metadata;
- ручная проверка того, что уже могло бы быть выражено в contract.

Не считать:

- простое чтение `review_brief.md`;
- одноразовое открытие approved package;
- явные контрольные действия из checklist, если они не требуют перепаковки данных.

### Reformatting Steps

Считать каждое ручное преобразование package-derived content в другой формат:

- переписывание findings в CRM field;
- разбиение recommendation на задачи вручную;
- перенос contradictions в отдельную заметку;
- ручная сборка коммерческого summary из нескольких export files.

### Missing Exports

Фиксировать конкретные отсутствующие export surfaces только в терминах workflow pain:

- какого именно artifact не хватило;
- какой ручной шаг он породил;
- повторялось ли это на нескольких audits.

### Operator Complaints

Фиксировать complaint только если он связан с конкретной boundary:

- `review_brief` недостаточен для review;
- `backlog.json` недостаточен для task import;
- prompt handoff требует ручной пересборки;
- summary export не закрывает CRM-adjacent use case.

## Scoring Bands

### Manual Tax Level

- `low`: `0-2` manual steps after approval
- `medium`: `3-5` manual steps after approval
- `high`: `6+` manual steps after approval

### Reformatting Tax Level

- `low`: `0-1` reformatting step
- `medium`: `2-3` reformatting steps
- `high`: `4+` reformatting steps

### Fit Assessment

- `good`: exports cover the workflow with no repeated pain
- `acceptable_with_gaps`: workflow is usable but has repeated manual friction
- `poor`: export layer is insufficient and repeatedly forces custom handling

## Integration Signals

### CRM Signal

- `none`: no repeated CRM-adjacent re-entry
- `weak`: occasional repeated copying into commercial tools
- `strong`: repeated structured data transfer into CRM-like tools across audits

### Task Tracker Signal

- `none`: backlog export is sufficient
- `weak`: some task reshaping still happens manually
- `strong`: repeated manual decomposition or field remapping into tracker workflows

### Direct Handoff Signal

- `none`: approved package + prompts are enough for AI handoff
- `weak`: some packaging notes are repeatedly added manually
- `strong`: repeated manual bundling or reformulation is required before every handoff

## Decision Use

Этот rubric должен читаться вместе с [scale-out-criteria.md](/Users/vadimevgrafov/neurosearch-analyzer/docs/06-delivery/scale-out-criteria.md), особенно с метриками:

- manual steps per audit after package approval;
- repeated operator complaints linked to a specific boundary.
