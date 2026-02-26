Разработал плейбук на основе репозитория Get Shit Done — https://github.com/gsd-build/get-shit-done (18K+ звёзд, используют инженеры из Amazon, Google, Shopify).

Залил его вместе с проектом, который разбирали на последнем заседании клуба.

Называется Phase Forge — фазовая разработка с ИИ от идеи до релиза.

Чем отличается от нашего ai-playbook:

▪️ Масштаб
ai-playbook: Задача → PR
Phase Forge: Идея → Фазы → Милестоун → Релиз

▪️ Context rot (деградация контекста)
ai-playbook: Не решается явно
Phase Forge: Свежий контекст для каждого плана

▪️ Параллелизм
ai-playbook: Нет
Phase Forge: Волновое выполнение (wave execution)

▪️ Верификация
ai-playbook: Чек-лист + тесты
Phase Forge: 3 уровня — авто + goal-backward + UAT

▪️ Отладка
ai-playbook: Минимальный фикс
Phase Forge: Персистентная сессия с DEBUG.md

▪️ Между сессиями
ai-playbook: handoff.md
Phase Forge: STATE.md + continue-here.md

Как использовать (процесс аналогичен ai-playbook):

1. Берёшь описание проекта → просишь агента инициализировать по промпту из 12-prompt-recipes.md (Промпт 1) → получаешь PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md

2. Просишь создать AGENTS.md по промпту 2

3. Для каждой фазы используешь промпты 3–6: discuss → plan → execute → verify

4. Для автономного выполнения — промпт 10 (аналог промпта из 12-agent-artifacts.md)
