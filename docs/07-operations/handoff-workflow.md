# Handoff Workflow

## Goal

Сделать pilot delivery steps явными и аудируемыми без мутации approved package artifacts.

## Output Location

Handoff workflow живет рядом с package, но вне него:

```text
<output_root>/
  audit_package/<audit_id>/
  handoff/<audit_id>/
    handoff_log.jsonl
    handoff_checklist.md
```

Это разделение сохраняет package immutable, но оставляет operational trail рядом с ним.

## Handoff Log

Формат: append-only `handoff_log.jsonl`

Каждая запись:

1. `event_id`
2. `audit_id`
3. `timestamp`
4. `event_type`
5. `actor`
6. `artifacts[]`
7. `notes`

Разрешенные `event_type`:

1. `package_approved`
2. `review_prepared`
3. `ai_handoff_sent`
4. `post_handoff_captured`

Правила:

- log append-only;
- event не должен переписывать package outputs;
- artifacts указываются относительными путями от output root;
- handoff event допускается только для approved package.

## Checklist

`handoff_checklist.md` генерируется детерминированно из approved package и напоминает оператору:

1. проверить `validate=completed`;
2. открыть `exports/review_brief.md`;
3. проверить `exports/backlog.json`;
4. подтвердить contradictions и top gaps;
5. передать package + prompts во внешний AI;
6. записать `ai_handoff_sent`;
7. после ответа AI записать `post_handoff_captured`.

## Commands

```text
python3 scripts/generate_handoff_checklist.py <audit_package_dir>
python3 scripts/record_handoff_event.py <audit_package_dir> --event-type review_prepared --actor presale-lead --artifact exports/review_brief.md
```

## Relationship To Existing Contracts

- approved package remains the evidence source;
- `exports/review_brief.*` remain review artifacts;
- handoff log records operational actions around those artifacts.

## Traceability

- Schema: [handoff_event.schema.json](/Users/vadimevgrafov/neurosearch-analyzer/schemas/handoff_event.schema.json)
- Delivery artifacts: [delivery-artifact-contracts.md](/Users/vadimevgrafov/neurosearch-analyzer/docs/03-architecture/delivery-artifact-contracts.md)
