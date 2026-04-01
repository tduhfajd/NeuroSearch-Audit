# Audit Lifecycle

## Goal

Зафиксировать единый контракт жизненного цикла аудита, чтобы intake, crawl, analyze и package слои работали через один и тот же `audit_id`, статусы и layout артефактов.

## Lifecycle Principles

- `audit_id` создается один раз на старте и не меняется в пределах полного прогона.
- Любой этап пишет артефакты только в область своего `audit_id`.
- Повторный расчет analysis/scoring на замороженных входах обязан сохранять воспроизводимость.
- Внешний AI получает только `approved package`, прошедший quality gates.

## Audit Identifier

- Формат: `aud_<timestamp>_<suffix>`.
- Требования:
1. глобально уникален в пределах хранилища;
2. пригоден для логов, путей и API-ответов;
3. не несет бизнес-семантики домена;
4. создается в intake слое до постановки задач в очередь.

Пример:

```text
aud_20260311T154500Z_f83k2m
```

## Audit State Model

### Top-level States

1. `accepted` — запрос принят и провалидирован.
2. `queued` — аудит поставлен в очередь на выполнение.
3. `crawling` — идет crawl и сбор raw artifacts.
4. `extracting` — техническое и смысловое извлечение данных.
5. `analyzing` — coverage, contradictions, scoring, recommendations.
6. `packaging` — сбор package и manifest.
7. `validating` — запуск quality gates.
8. `completed` — пакет собран и одобрен.
9. `failed` — аудит остановлен из-за ошибки.
10. `cancelled` — аудит остановлен пользователем или системой.

### Stage Status Rules

- Переходы однонаправленные, кроме управляемого retry внутри этапа.
- Ошибки этапов фиксируются в `stage_runs[]` с кодом, сообщением и retry metadata.
- `completed` разрешен только после `validating`.
- `failed` сохраняет последние успешно собранные артефакты и причину остановки.

## Runtime Execution State

`audit.Record` недостаточен для live execution, потому что package artifacts не должны использоваться как mutable orchestrator state. Поэтому для MVP-2 вводится отдельный runtime layer:

1. `audit.Record` — intake-facing и lifecycle-facing запись;
2. `runtime/<audit_id>/attempts/<nnn>/run_state.json` — mutable execution state конкретного attempt;
3. `audit_package/<audit_id>/manifest.json` — immutable package integrity record.

Runtime state хранит:

- attempt number;
- executable stage states;
- transition log;
- last error;
- timestamps старта/обновления/завершения.

Это позволяет:

- запускать audit pipeline как staged runtime;
- сохранять failed state без мутации approved package;
- добавлять resume/retry semantics через новый attempt, а не через скрытую перезапись package outputs.

## Audit Record Contract

Минимальные поля аудита:

1. `audit_id`
2. `submitted_url`
3. `normalized_host`
4. `status`
5. `ruleset_version`
6. `schema_version`
7. `created_at`
8. `updated_at`
9. `stage_runs[]`
10. `package_status`

## Stage Run Contract

Каждый этап фиксирует:

1. `stage`
2. `status`
3. `started_at`
4. `finished_at`
5. `attempt`
6. `worker_id`
7. `inputs`
8. `outputs`
9. `error_code`
10. `error_message`

## Package Layout

```text
audit_package/
  <audit_id>/
    manifest.json
    audit.json
    crawl/
      visited_urls.json
      fetch_log.json
      link_graph.json
    pages/
      raw/
      rendered/
      technical/
    analysis/
      page_blocks.json
      entities.json
      entity_graph.json
      coverage_report.json
      contradictions.json
      ai_readiness_scores.json
      recommendations.json
    prompts/
      client-report.md
      technical-report.md
      optimization-plan.md
      implementation-backlog.md
      commercial-proposal.md

runtime/
  <audit_id>/
    attempts/
      001/
        run_state.json
```

## Artifact Ownership By Stage

- `accepted`, `queued`: intake/scheduler metadata only.
- `crawling`: `crawl/*` and raw page artifacts.
- `extracting`: `pages/technical/*`, rendered snapshots, `analysis/page_blocks.json`.
- `analyzing`: `entities.json`, `entity_graph.json`, `coverage_report.json`, `contradictions.json`, `ai_readiness_scores.json`, `recommendations.json`.
- `packaging`: `manifest.json`, file inventory, package status.
- `validating`: gate reports and final approval marker.

## Retry And Reproducibility Rules

- Retry допускается на уровне этапа, а не через переиспользование частично мутированных артефактов без явного статуса.
- Derived artifacts должны ссылаться на входные артефакты по пути и версии.
- Manifest обязан фиксировать `ruleset_versions`, `schema_versions` и stage completion timestamps.
- Повторный scoring на тех же `page_blocks/entities/coverage/contradictions` должен давать идентичный output, кроме служебных timestamp полей.

## Failure Semantics

- `failed` не удаляет существующие артефакты автоматически.
- Ошибка quality gate переводит `package_status` в `rejected`, но сохраняет пакет для диагностики.
- Этапы с неполным evidence не могут поднимать severity findings до approved output.

## Open Decisions For Later Phases

- Где физически хранить raw blobs: filesystem, object storage, or hybrid.
- Как кодировать partial reruns для локальных repair-проходов.
- Нужен ли отдельный `approval` state для ручного пресейл-review перед AI handoff.
- Нужен ли heartbeat/update lease для long-running stages beyond simple timestamps.

## Related Artifacts

- [Data Contracts](/Users/vadimevgrafov/neurosearch-analyzer/docs/03-architecture/data-contracts.md)
- [Integration Points](/Users/vadimevgrafov/neurosearch-analyzer/docs/03-architecture/integration-points.md)
- [Runtime Execution Contracts](/Users/vadimevgrafov/neurosearch-analyzer/docs/03-architecture/runtime-execution-contracts.md)
- [System Architecture](/Users/vadimevgrafov/neurosearch-analyzer/docs/03-architecture/system-architecture.md)
