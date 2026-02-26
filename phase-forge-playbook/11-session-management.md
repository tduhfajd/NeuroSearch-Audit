# Управление сессиями: STATE.md, пауза, возобновление

Проекты длятся несколько сессий. Потеря контекста между ними —
главная причина деградации качества. Phase Forge решает это через
структурированные артефакты сессий.

---

## STATE.md — живая память проекта

STATE.md — единственный файл, который нужно прочитать, чтобы понять
"где мы, что было и что дальше".

### Содержание

```markdown
# Project State

## Project Reference
See: .planning/PROJECT.md (updated 2025-01-20)
Core value: Пользователи делятся контентом с единомышленниками
Current focus: Phase 3 — Post Feed

## Current Position
Phase: 3 of 6 (Post Feed)
Plan: 2 of 3 in current phase
Status: In progress
Last activity: 2025-01-20 — Завершён план 03-01 (модели)
Progress: [████░░░░░░] 40%

## Performance Metrics
Total plans completed: 5
Average duration: 35 min
Total execution time: 2.9 hours

## Accumulated Context

### Decisions
- Phase 2: Выбрали card layout вместо timeline
- Phase 3: Infinite scroll вместо pagination

### Pending Todos
2 pending — see /gsd:check-todos

### Blockers/Concerns
- Нет блокеров.

## Session Continuity
Last session: 2025-01-20 14:30
Stopped at: Завершён план 03-01, готов к выполнению 03-02
Resume file: .planning/phases/03-post-feed/.continue-here.md
```

### Правила

- **Размер:** < 100 строк. Это дайджест, не архив.
- **Чтение:** первый шаг каждого воркфлоу.
- **Запись:** после каждого значимого действия.
- **Решения:** недавние решения (3-5) в краткой форме. Полный лог в PROJECT.md.
- **Блокеры:** только активные. Решённые — удалять.

---

## Пауза работы

Когда заканчиваешь сессию — создай `.continue-here.md`:

```markdown
---
phase: 03-post-feed
task: 3
total_tasks: 7
status: in_progress
last_updated: 2025-01-20T14:30:00Z
---

<current_state>
Завершены планы 03-01 и 03-02. Начат 03-03 (интеграция).
Задача 3 из 7 в процессе.
</current_state>

<completed_work>
- Task 1: Модель Post — Done
- Task 2: API endpoints — Done
- Task 3: Feed component — In progress, загрузка работает
</completed_work>

<remaining_work>
- Task 3: Feed component — осталось: пагинация + empty state
- Task 4: Like button — Not started
- Task 5: Integration tests — Not started
</remaining_work>

<decisions_made>
- Выбрали infinite scroll (не pagination) — лучше для мобильных
- Card компонент из shadcn/ui — подходит по дизайну
</decisions_made>

<blockers>
Нет.
</blockers>

<context>
Фид загружает первые 20 постов. Нужно добавить intersection observer
для подгрузки следующих. Empty state — когда нет подписок.
</context>

<next_action>
Добавить IntersectionObserver в FeedList для infinite scroll.
</next_action>
```

### Правила `.continue-here.md`
- Достаточно конкретно, чтобы свежий агент понял немедленно.
- Включай ПОЧЕМУ приняты решения (не пересматривать в следующей сессии).
- `<next_action>` — конкретное действие без необходимости читать что-то ещё.
- Файл **удаляется** после возобновления.

---

## Возобновление работы

### Алгоритм восстановления

1. Прочитать STATE.md → общая картина.
2. Проверить `.continue-here.md` → точная позиция.
3. Представить статус пользователю.
4. Определить следующее действие.
5. Маршрутизировать к соответствующему воркфлоу.

### Что показать пользователю

```
📍 Phase 3 of 6: Post Feed
📋 Plan 03-03 in progress (task 3/7)
⏰ Last session: 2025-01-20 14:30
📝 Stopped at: Feed component — infinite scroll

Next: Добавить IntersectionObserver для infinite scroll.
```

---

## Очистка контекста

### Когда чистить
- Между фазами (обязательно).
- При падении качества генерации.
- После длинных обсуждений.
- Перед сложными задачами.

### Как чистить
1. Обнови STATE.md.
2. Создай `.continue-here.md` (если mid-phase).
3. `/clear` в Claude Code.
4. Начни новую сессию с resume-work.

### Почему это важно
Phase Forge спроектирован вокруг свежих контекстов.
Каждый подагент получает чистое окно. Основная сессия тоже
должна оставаться чистой для оркестрации.

---

## Todos (захват идей)

Во время работы часто возникают идеи, не относящиеся к текущей задаче.
Не теряй их, но и не отвлекайся:

```markdown
# .planning/todos/pending/add-dark-mode.md

## Idea
Добавить тёмную тему. Пользователи просят в отзывах.

## Context
Возникло при работе над Phase 3 (Post Feed) — заметил,
что цветовые переменные уже организованы для темы.

## Priority
Nice to have. Может быть в v1.1.
```

Просмотр: `ls .planning/todos/pending/`
Выполнение: перенести в done после реализации.

---

## Шаблоны

- [`templates/STATE.md`](./templates/STATE.md)
- [`templates/continue-here.md`](./templates/continue-here.md)
