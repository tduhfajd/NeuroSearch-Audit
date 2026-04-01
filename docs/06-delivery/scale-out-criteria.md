# Scale-Out Criteria

## Goal

Сделать решения о переходе к deferred components измеримыми. Этот документ не рекомендует немедленный переход, а фиксирует условия, при которых он оправдан.

## Decision Rule

Переход к новой инфраструктурной или модульной сложности допустим только при выполнении обоих условий:

1. есть повторяемый operational symptom на benchmark или pilot usage;
2. текущий MVP-friendly вариант не закрывается локальной оптимизацией без изменения архитектуры.

## Queue / Broker

### Keep `Redis Streams`

- если p95 pipeline latency приемлема для pilot SLA;
- если retry and delivery semantics достаточны;
- если backlog очереди не растет стабильно между запусками.

### Consider `RabbitMQ`

- если backlog очереди стабильно растет в нескольких прогонах подряд;
- если нужны richer routing semantics than current queue model;
- если delivery guarantees становятся причиной ручных recovery действий;
- если benchmark показывает, что проблема не в worker throughput, а именно в broker behavior.

## Storage

### Keep current package/file + `PostgreSQL` path

- если package artifacts читаются и валидируются без operational friction;
- если audit lookup и package assembly не упираются в storage latency;
- если analytics usage остается умеренной и не требует тяжелых cross-audit aggregations.

### Consider `ClickHouse`

- если появляются регулярные product questions across many audits, которые неудобно или дорого считать из package files/`PostgreSQL`;
- если pilot stakeholders требуют дешевые wide aggregations by market, page type, contradiction class, or score buckets;
- если benchmark или pilot review показывает, что analytical queries становятся bottleneck.

## Rendering

### Keep current isolated renderer boundary

- если JS-heavy pages обрабатываются точечно и не доминируют load profile;
- если browser orchestration overhead не является top operational risk.

### Consider dedicated render pool/service hardening

- если render queue становится отдельным bottleneck;
- если browser lifecycle failures materially affect throughput or stability;
- если pilot usage показывает значимую долю pages requiring render.

## Semantic / Analysis Layer

### Keep current Python rule-based path

- если rule tuning still produces explainable gains;
- если deterministic outputs remain reproducible and reviewable;
- если current artifact set supports presale and delivery usage.

### Consider deeper module split or specialized services

- если a single analysis package accumulates unrelated responsibilities and slows changes materially;
- если certain hot paths need independent scaling or release cadence;
- если benchmark evidence shows one analysis substage dominates runtime or defect rate.

## Integration Work

### Keep file-based exports

- если presale and delivery teams can consume `exports/*.json` without major manual pain;
- если there is no proven repeated demand for direct CRM/task-tracker writes.

### Consider live integrations

- если manual transfer from exports becomes a repeated operational tax in pilots;
- если target systems and field mappings stabilize across multiple pilot users;
- если integration value exceeds the maintenance and auth/security cost.

## Metrics To Review

- package approval pass rate;
- reproducibility pass rate;
- p50/p95 pipeline duration;
- queue backlog growth between runs;
- render-required page ratio;
- manual steps per audit after package approval;
- repeated operator complaints linked to a specific boundary.

## Explicit Non-Trigger Cases

- curiosity about new infrastructure;
- one-off slow run without repetition;
- isolated feature requests from a single prospect without benchmark support;
- vague expectations that enterprise tooling is “more serious”.

## Review Cadence

- revisit after each pilot batch or benchmark expansion;
- record the observed trigger and the chosen response in planning/state artifacts before changing architecture.
