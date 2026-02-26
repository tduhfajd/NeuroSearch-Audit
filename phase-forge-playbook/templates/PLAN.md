---
phase: X
plan: Y
title: "[Краткое название]"
wave: 1
depends_on: []
files_modified:
  - path/to/file1.ext
  - path/to/file2.ext
autonomous: true
---

# Phase X, Plan Y: [Название]

## Objective

[Что этот план доставляет — 1-2 предложения]

## must_haves

[Из Success Criteria фазы — что ОБЯЗАНО быть выполнено]

1. [Критерий 1 — наблюдаемое поведение]
2. [Критерий 2 — наблюдаемое поведение]

## Tasks

<task type="auto">
  <name>[Название задачи 1]</name>
  <files>[путь/к/файлам]</files>
  <action>
    [Конкретные инструкции: что сделать, какой подход использовать,
    какие паттерны применить. Точно и однозначно.]
  </action>
  <verify>[Команда проверки: pytest, curl, lint — что запустить]</verify>
  <done>[Критерий завершения: что должно быть true]</done>
</task>

<task type="auto">
  <name>[Название задачи 2]</name>
  <files>[путь/к/файлам]</files>
  <action>
    [Конкретные инструкции]
  </action>
  <verify>[Команда проверки]</verify>
  <done>[Критерий завершения]</done>
</task>

<task type="human-verify">
  <name>[Название задачи 3 — требует ручной проверки]</name>
  <files>[путь/к/файлам]</files>
  <action>
    [Конкретные инструкции]
  </action>
  <verify>[Описание что проверить вручную]</verify>
  <done>[Критерий завершения]</done>
</task>

## Verification

После завершения всех задач:
- [ ] `[команда тестов]` — все тесты зелёные
- [ ] `[команда линтера]` — нет ошибок
- [ ] must_haves выполнены (evidence выше)

## Notes

[Дополнительный контекст для исполнителя, если нужен.
Ссылки на CONTEXT.md, RESEARCH.md, конвенции проекта.]
