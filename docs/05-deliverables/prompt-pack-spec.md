# Prompt Pack Spec

## Goal
Определить единый стандарт промтов для внешнего AI-агента, чтобы из `audit_package` воспроизводимо генерировать 5 типов документов без выдумывания данных.

## Prompt Files
1. `prompts/client_report_prompt.md`
2. `prompts/tech_audit_prompt.md`
3. `prompts/optimization_plan_prompt.md`
4. `prompts/work_backlog_prompt.md`
5. `prompts/commercial_offer_prompt.md`

## Required Prompt Sections
- `Role`: кто пишет документ (например, presale lead / tech lead).
- `Audience`: для кого документ.
- `Allowed Inputs`: список разрешенных JSON-файлов.
- `Document Structure`: обязательные разделы.
- `Evidence Rules`: формат ссылок URL/finding_id/score.
- `No Fabrication Policy`: запрет на домысливание.
- `Output Constraints`: язык, стиль, объем.

## Evidence Format
- `Evidence: [url=<...>; finding=<...>; source=<file>; score=<...>]`
- Если данных нет: `Evidence: [data_gap=<описание>]`

## Anti-hallucination Rules
- Любой high-impact claim без evidence должен быть переписан как гипотеза.
- Запрещено ссылаться на файлы вне `audit_package`.
- Противоречивые факты должны выноситься отдельным блоком “Нужна верификация”.

## Generation Flow
1. Prompt Generator формирует 5 промтов.
2. Пакет передается внешнему AI.
3. AI генерирует документы.
4. Evidence Validator проверяет ссылочную целостность.
5. Документы помечаются `approved` или `needs_revision`.

## Versioning
- `prompt_pack_version`
- `ruleset_version`
- `schema_version`

## Facts
- В `idea.md` зафиксировано: система должна выдавать и данные, и промты для любого AI-агента.

## Assumptions
- Первый язык промтов — русский, с возможностью локализации.

## Hypotheses
- Стандартизированный prompt pack уменьшит расхождение между разными AI-провайдерами.

## Open Questions
- Нужен ли отдельный post-processor для унификации стиля документов разных моделей.

## Traceability
- `idea.md`: секции про “dataset + prompts”, независимость от конкретной AI-модели и требования не выдумывать факты.
