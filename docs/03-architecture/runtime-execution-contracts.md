# Runtime Execution Contracts

## Goal

Отделить mutable runtime state от immutable `audit_package`, чтобы живой прогон аудита можно было запускать, останавливать, диагностировать и возобновлять без мутации финальных package artifacts.

## Runtime State Object

Базовый runtime contract хранится как `run_state.json` вне `audit_package` и описывает один attempt выполнения для конкретного `audit_id`.

Обязательные поля:

1. `schema_version`
2. `audit_id`
3. `attempt`
4. `status`
5. `submitted_url`
6. `normalized_host`
7. `ruleset_version`
8. `started_at`
9. `updated_at`
10. `stages[]`
11. `transitions[]`

## Stage Model

Исполнимые runtime stages для MVP-2:

1. `crawling`
2. `extracting`
3. `analyzing`
4. `packaging`
5. `validating`

Правила:

- стадии идут в фиксированном порядке;
- новая стадия не стартует, пока предыдущая не имеет `completed`;
- `failed` делает весь run terminal до явного нового attempt;
- `completed` разрешен только после `validating`.

## Stage State Contract

Каждая stage entry хранит:

1. `stage`
2. `status`
3. `attempt`
4. `max_attempts`
5. `retry_count`
6. `worker_id`
7. `started_at`
8. `finished_at`
9. `inputs[]`
10. `outputs[]`
11. `error_code`
12. `error_message`
13. `retry_history[]`

Это runtime-слой, а не package contract: он может меняться между попытками, но не должен переписывать уже собранные approved artifacts.

## Transition Log

`transitions[]` фиксирует ключевые runtime events:

1. `initialized`
2. `stage_started`
3. `stage_completed`
4. `stage_failed`
5. `stage_retried`

Назначение transition log:

- понять, где именно остановился прогон;
- иметь минимальный audit trail без отдельного tracing stack;
- не выводить operator diagnostics из косвенных package изменений.

## Persistence Layout

```text
runtime/
  <audit_id>/
    attempts/
      001/
        run_state.json
      002/
        run_state.json
```

Правила:

- каждый attempt получает собственный путь;
- `audit_package/<audit_id>/` остается immutable output area;
- runtime persistence может ссылаться на package artifacts по path, но не наоборот.

## Relationship To Existing Contracts

- `audit.Record` остается intake-facing lifecycle record.
- `run_state.json` становится execution-facing state record.
- `manifest.json` остается package integrity record.

То есть:

- `audit.Record` отвечает на вопрос "что запросили";
- `run_state.json` отвечает на вопрос "как исполняется текущая попытка";
- `manifest.json` отвечает на вопрос "что собрано и одобрено".

## Failure And Retry Semantics

- stage failure сохраняет `last_error` и terminal `failed` status на уровне run state;
- failure не обязан удалять уже созданные промежуточные artifacts;
- новый retry создается как новый attempt, а не мутация истории предыдущего.

Для bounded in-attempt retries:

- retry возможен только для явно retryable stage errors;
- retry limit задается runtime policy и сохраняется как `max_attempts` на уровне stage state;
- каждый retry фиксируется в `retry_history[]` и `stage_retried` transition;
- если лимит исчерпан, stage переходит в terminal `failed` как раньше.

## Traceability

- Schema: [runtime_run_state.schema.json](/Users/vadimevgrafov/neurosearch-analyzer/schemas/runtime_run_state.schema.json)
- Lifecycle: [audit-lifecycle.md](/Users/vadimevgrafov/neurosearch-analyzer/docs/03-architecture/audit-lifecycle.md)
