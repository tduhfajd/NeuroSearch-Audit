# Repository Layout

## Goal

Определить стартовую структуру репозитория и границы сервисов так, чтобы реализация `Go`-ядра и `Python`-аналитики шла через явные контракты, а не через смешение ответственности.

## Top-Level Layout

```text
cmd/
  api/                 # intake/status API entrypoint
  worker/              # background worker entrypoint for crawl-stage orchestration
internal/
  audit/               # audit lifecycle, IDs, stage state, package metadata
  crawl/               # queue consumer, fetch, discovery, crawl policies
  platform/            # config, logging, metrics, shared runtime plumbing
  storage/             # PostgreSQL and artifact persistence adapters
python/
  common/              # shared Python utilities, contracts, validation helpers
  semantic/            # page type and block extraction
  analysis/            # entities, coverage, contradictions, scoring, recommendations
configs/               # local config examples and environment wiring
schemas/               # JSON Schema contracts shared across modules
scripts/               # validation and developer utility scripts
testdata/
  fixtures/            # HTML, JSON, and package fixtures for tests
docs/                  # product and architecture documents
.planning/             # execution system and phase artifacts
```

## Boundary Rules

### `cmd/`

- Только entrypoints.
- Никакой доменной логики, кроме wiring и startup.

### `internal/audit`

- Владелец `audit_id`, lifecycle state transitions, and package metadata contracts.
- Не содержит crawl-specific fetch logic.

### `internal/crawl`

- Владелец crawl queue orchestration, URL policies, visited set logic, and raw acquisition.
- Может писать raw artifacts через storage contracts, но не интерпретирует semantic findings.

### `internal/storage`

- Владелец persistence adapters for PostgreSQL and artifact blobs.
- Не должен знать scoring formulas or semantic rules.

### `internal/platform`

- Cross-cutting runtime primitives: config loading, structured logging, metrics, tracing helpers.
- Никаких feature-specific business rules.

### `python/semantic`

- Владелец `page_type` and block extraction.
- Получает normalized page inputs, не управляет crawl scheduling.

### `python/analysis`

- Владелец entities, contradictions, coverage, scoring, and recommendations.
- Работает на versioned artifact inputs; не пишет raw crawl state.

### `python/common`

- Shared contract readers, validators, and helper code.
- Не должен превращаться в мусорный слой с feature logic.

## Integration Strategy

- Cross-language handoff идет через persisted artifacts and schemas, not direct in-process calls.
- `Go` produces stable crawl and technical outputs.
- `Python` consumes those outputs and emits versioned analysis artifacts.
- Package builder can live in either runtime later, but must obey `manifest.schema.json`.

## Service Candidates By Phase

- Phase 02:
  - `cmd/api`
  - `cmd/worker`
  - `internal/audit`
  - `internal/crawl`
  - `internal/storage`
- Phase 03:
  - renderer adapter
  - `python/semantic`
- Phase 04:
  - `python/analysis`

## Configuration Boundaries

- `configs/` stores checked-in examples only.
- Runtime secrets stay in environment variables or local untracked files.
- Ruleset version, schema version, and queue/storage settings should be explicit config values.

## Testing Boundaries

- `testdata/fixtures` stores deterministic fixture inputs and expected artifacts.
- `Go` tests target crawl/core contracts.
- `Python` tests target schema-valid outputs and deterministic analysis rules.
- Cross-language contract validation should rely on schema fixtures rather than shared in-memory mocks.

## Near-Term Scaffolding Guidance

- First code session should create the `Go` module and Python package metadata in the directories defined here.
- Avoid creating renderer and analysis implementations before Phase 02 and Phase 03 contracts are wired.
- New directories should be added only when they map to a module or cross-cutting concern already documented in the roadmap.
