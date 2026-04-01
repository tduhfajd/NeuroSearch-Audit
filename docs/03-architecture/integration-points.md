# Integration Points

## I-001 Audit Intake API
- Тип: внутренний API.
- Назначение: старт аудита.
- Вход: URL, настройки обхода, ruleset version.
- Выход: `audit_id`, статус.

## I-002 Crawl Data Storage
- Тип: хранилище артефактов.
- Назначение: сохранить raw/rendered/parsed данные.
- Требование: доступ для повторного анализа и аудита качества.

## I-003 Scoring/Rules Registry
- Тип: конфигурационный сервис.
- Назначение: выдача правил coverage/scoring по версии.
- Требование: воспроизводимость результатов.

## I-004 External AI Handoff
- Тип: внешний интерфейс передачи package.
- Назначение: генерация документов любым AI-агентом.
- Формат: `audit_package/<audit_id>/` + `prompts/`.

## I-005 CRM/Presale Export (Post-MVP)
- Тип: интеграция с коммерческими системами.
- Назначение: передача LVI, статуса и КП метаданных.
- Примечание: опционально для ранних релизов.
 - MVP bridge: file-based export from approved package via `exports/summary.json`.

## I-006 Task Tracker Export
- Тип: интеграция с Jira/GitLab.
- Назначение: выгрузка технического backlog.
- Требование: перенос `priority`, `acceptance criteria`, `evidence links`.
 - MVP bridge: file-based export via `exports/backlog.json`.
 - Current candidate: narrow one-way task creation integration derived from `exports/backlog.json`.

## I-007 Observability Sink
- Тип: логи/метрики/трейсы.
- Назначение: контроль SLA и диагностика.
- Требование: метрики по этапам crawl/parse/analyze/package.

## Interface Contract Rules
- Каждая интеграция обязана использовать `audit_id` как сквозной идентификатор.
- Внешний AI получает только approved package после quality gates.
- Источники фактов неизменяемы внутри жизненного цикла `audit_id`.
- File-based exports derive only from approved package artifacts and do not mutate package contents.

## Security Notes
- Права доступа на пакеты ограничиваются ролями.
- Передача пакета во внешний AI должна логироваться.

## Facts
- В `idea.md` явно отражено: генерация документов не привязана к конкретной AI-модели.

## Assumptions
- В MVP интеграция с внешним AI может быть полуавтоматической (через экспорт файлов).

## Hypotheses
- Экспорт backlog в трекер снизит ручные операции после продажи проекта.

## Open Questions
- Какие приоритетные CRM/PM-интеграции нужны первыми для пилота.
- Какой конкретный task tracker станет первым target для pilot-safe write integration.

## Traceability
- `idea.md`: блоки об архитектуре “deterministic core + любой AI-агент”, prompt pack и практическом использовании в агентском процессе.
