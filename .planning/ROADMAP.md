# Roadmap: NeuroSearch Audit

## Overview

Семь последовательных фаз: начинаем с фундамента (проект + БД), затем строим краулер, rule-based анализатор, AI Bridge через ChatGPT Playwright, дашборд, генератор отчётов и финальную интеграцию с КП. Каждая фаза даёт рабочий, тестируемый результат. После Phase 6 инструмент готов к реальным аудитам.

## Phases

- [x] **Phase 1: Foundation** — проектная структура, БД схема, базовый FastAPI сервер
- [ ] **Phase 2: Crawler** — краулер сайта (HTTP + Playwright), сбор HTML/мета/schema
- [ ] **Phase 3: Analyzer** — rule-based анализатор (20+ проверок), скоринг, карта проблем
- [ ] **Phase 4: AI Bridge** — Playwright → ChatGPT Plus, AI-оценка страниц, AVRI
- [ ] **Phase 5: Dashboard** — веб-интерфейс: запуск аудита, просмотр результатов, прогресс
- [ ] **Phase 6: Reports** — генератор PDF-отчёта и КП (3 пакета)
- [ ] **Phase 7: Polish** — интеграционные тесты, edge cases, финальная шлифовка

---

## Phase Details

### Phase 1: Foundation
**Goal**: Рабочая основа — структура проекта, схема БД, запущенный локальный сервер
**Depends on**: Nothing
**Requirements**: CRL-01 (частично), SCR-01 (структуры данных)
**Success Criteria**:
  1. `uvicorn backend.main:app` запускается без ошибок на порту 8000
  2. PostgreSQL запущен локально, все таблицы созданы через Alembic migration
  3. `GET /health` возвращает `{"status": "ok"}`
  4. Структура директорий соответствует `neurosearch-audit-tool.md §11`
**Plans**: Complete

Plans:
- [x] 01-01: Инициализация проекта — `pyproject.toml` (uv), `.env.example`, `.gitignore`
- [x] 01-02: Схема БД — модели SQLAlchemy: `audits`, `pages`, `issues`, `reports`
- [x] 01-03: Alembic migration — создание всех таблиц
- [x] 01-04: FastAPI skeleton — `main.py`, роутеры `/audits`, `/health`
- [x] 01-05: Docker Compose (опционально) или инструкция `brew services start postgresql@16`

---

### Phase 2: Crawler
**Goal**: Инструмент умеет обходить сайт, собирать данные и сохранять их в БД
**Depends on**: Phase 1
**Requirements**: CRL-01, CRL-02, CRL-03, CRL-04, CRL-05
**Success Criteria**:
  1. Запуск `POST /audits` с URL домена → краулинг завершается, в таблице `pages` записаны ≥50 страниц тестового сайта
  2. Для каждой страницы сохранены: status_code, title, h1, meta_description, canonical, robots_meta, json_ld, word_count, inlinks_count
  3. `robots.txt` и `sitemap.xml` проверены и статус записан в `audits.meta`
  4. JS-страница (контент в DOM через React/Vue) корректно краулится через Playwright
  5. PageSpeed score собран для топ-10 страниц по inlinks_count
**Plans**: TBD

Plans:
- [ ] 02-01: Базовый HTTP краулер — Scrapy spider, очередь URL, depth limit
- [ ] 02-02: Парсинг страницы — title, h1, meta, canonical, robots meta, ссылки
- [ ] 02-03: Парсинг JSON-LD — извлечение всех schema.org блоков
- [ ] 02-04: Playwright интеграция — headless Chromium для JS-сайтов
- [ ] 02-05: robots.txt + sitemap.xml checker
- [ ] 02-06: PageSpeed API / Lighthouse CLI для топ-10 страниц
- [ ] 02-07: Сохранение результатов в PostgreSQL (bulk insert)

---

### Phase 3: Analyzer
**Goal**: Rule-based анализатор находит проблемы и присваивает приоритеты P0–P3
**Depends on**: Phase 2
**Requirements**: ANA-01, ANA-02, ANA-03, ANA-04, ANA-05, ANA-06, ANA-07, ANA-08, SCR-01, SCR-03
**Success Criteria**:
  1. После краулинга запускается `POST /audits/{id}/analyze` → таблица `issues` заполнена
  2. Все 8 категорий проверок (ANA-01–08) работают корректно на тестовых данных
  3. SEO Tech Health Score рассчитан (0–100) и записан в `audits.seo_score`
  4. Каждая проблема имеет: тип, описание, приоритет (P0/P1/P2/P3), affected_url
  5. `GET /audits/{id}/issues` возвращает сгруппированный список проблем по приоритету
**Plans**: TBD

Plans:
- [ ] 03-01: Движок проверок — базовый класс `Rule`, реестр правил
- [ ] 03-02: Индексация — noindex, robots.txt disallow, canonical checks (ANA-01, 04)
- [ ] 03-03: Дубли — title/h1 дубли, короткие/длинные мета (ANA-02, 03)
- [ ] 03-04: Ссылки — битые, редиректы-цепочки (ANA-05)
- [ ] 03-05: Schema.org — наличие типов, валидация полей (ANA-06, 07)
- [ ] 03-06: Trust signals — коммерческие страницы (ANA-08)
- [ ] 03-07: SEO Tech Health Score — весовая формула, нормализация 0–100
- [ ] 03-08: API эндпоинт `GET /audits/{id}/issues` с группировкой по приоритету

---

### Phase 4: AI Bridge
**Goal**: Инструмент отправляет страницы в ChatGPT Plus и получает структурированные AI-оценки
**Depends on**: Phase 2 (нужны данные страниц)
**Requirements**: AIB-01, AIB-02, AIB-03, AIB-04, AIB-05, SCR-02
**Success Criteria**:
  1. `python backend/analyzer/ai_bridge.py --setup` открывает браузер → после ручного логина сессия сохраняется в `chatgpt_session/storage_state.json`
  2. Запуск AI-анализа для аудита → 10 страниц оценены, результаты в `pages.ai_scores` (JSON)
  3. Каждая страница получила оценки 0–10 по 5 метрикам + текстовые рекомендации
  4. AVRI рассчитан и записан в `audits.avri_score`
  5. При rate limit — запросы ставятся в очередь с задержкой, нет падений
  6. При просроченной сессии — понятное сообщение в UI "Требуется переавторизация"
**Plans**: TBD

Plans:
- [ ] 04-01: Playwright setup — headless браузер, загрузка/сохранение storage_state
- [ ] 04-02: ChatGPT interaction — отправка промпта, ожидание ответа, парсинг
- [ ] 04-03: Промпт-шаблон — структурированный JSON-ответ с 5 метриками + рекомендации
- [ ] 04-04: Очередь с rate limiting — RQ job, задержки ≥15 сек между запросами
- [ ] 04-05: Session health check — проверка сессии перед запуском, уведомление при необходимости
- [ ] 04-06: AVRI расчёт — агрегация оценок 10 страниц по формуле
- [ ] 04-07: Сохранение AI-результатов в БД

---

### Phase 5: Dashboard
**Goal**: Рабочий веб-интерфейс для запуска аудитов и просмотра результатов
**Depends on**: Phase 3, Phase 4
**Requirements**: UI-01, UI-02, UI-03, UI-04
**Success Criteria**:
  1. `http://localhost:8000` открывается в браузере — список аудитов виден
  2. Форма нового аудита заполнена и отправлена → аудит стартует, прогресс-бар обновляется
  3. Страница результатов показывает: SEO Score, AVRI, карту проблем P0–P3
  4. Каждая проблема раскрывается — видно описание и рекомендацию
  5. UI работает без JavaScript-фреймворка (HTML + Tailwind + Alpine.js)
**Plans**: TBD

Plans:
- [ ] 05-01: Layout — header, nav, base Tailwind стили
- [ ] 05-02: Список аудитов — таблица с доменом, датой, scores, статусом
- [ ] 05-03: Форма нового аудита — валидация URL, выбор параметров
- [ ] 05-04: Прогресс-бар — polling `GET /audits/{id}/status` каждые 2 сек
- [ ] 05-05: Страница результатов — три панели: Tech Health, AI Readiness, Issues
- [ ] 05-06: Issue Map — accordion по приоритетам P0/P1/P2/P3

---

### Phase 6: Reports
**Goal**: Инструмент генерирует PDF-отчёт и КП, готовые для отправки клиенту
**Depends on**: Phase 3, Phase 4, Phase 5
**Requirements**: REP-01, REP-02, REP-03, REP-04
**Success Criteria**:
  1. `GET /audits/{id}/report/pdf` → скачивается PDF-файл
  2. PDF содержит: Executive Summary, Tech Health (с числами из анализатора), AI Readiness, Issue Map, Recommendations
  3. Текстовые части (описание проблем, рекомендации) сгенерированы ChatGPT на основе данных аудита
  4. КП автоматически выбирает релевантный пакет (Start/Growth/Authority) по карте проблем
  5. PDF выглядит профессионально — читаем без контекста, можно отправить клиенту
**Plans**: TBD

Plans:
- [ ] 06-01: Jinja2 шаблон — HTML структура отчёта
- [ ] 06-02: WeasyPrint конфигурация — стили, шрифты, кириллица
- [ ] 06-03: Executive Summary — автогенерация через ChatGPT (3–5 предложений)
- [ ] 06-04: Issue Section — детальный список проблем с описаниями
- [ ] 06-05: Логика выбора КП пакета — Start/Growth/Authority по составу P0/P1/P2 проблем
- [ ] 06-06: КП секция — описание пакета, работы, ожидаемый эффект
- [ ] 06-07: API эндпоинт `GET /audits/{id}/report/pdf` + кнопка в UI

---

### Phase 7: Polish
**Goal**: Стабильный, надёжный инструмент без критических edge cases
**Depends on**: Phase 6
**Requirements**: все v1
**Success Criteria**:
  1. Аудит сайта с 200+ страницами проходит без падений от начала до PDF
  2. Повторный запуск аудита того же домена — старые данные не конфликтуют с новыми
  3. Краулинг JS-тяжёлого сайта (SPA) завершается корректно (timeout обработан)
  4. ChatGPT rate limit — очередь ждёт и продолжает без ручного вмешательства
  5. Документация: README с командами установки и запуска
**Plans**: TBD

Plans:
- [ ] 07-01: Error handling — краулер (timeout, 5xx), AI Bridge (rate limit, session), report
- [ ] 07-02: Повторный аудит — upsert страниц, не дублировать issues
- [ ] 07-03: SPA timeout обработка — Playwright wait strategies
- [ ] 07-04: README — установка, первый запуск, setup ChatGPT сессии
- [ ] 07-05: Финальный end-to-end прогон на реальном сайте

---

## Progress

**Порядок выполнения:** 1 → 2 → 3 → 4 → 5 → 6 → 7

| Phase | Plans Complete | Status | Completed |
|-------|---------------|--------|-----------|
| 1. Foundation | 5/5 | Complete | 2026-02-26 |
| 2. Crawler | 0/7 | Not started | - |
| 3. Analyzer | 0/8 | Not started | - |
| 4. AI Bridge | 0/7 | Not started | - |
| 5. Dashboard | 0/6 | Not started | - |
| 6. Reports | 0/7 | Not started | - |
| 7. Polish | 0/5 | Not started | - |

**Итого: 45 планов · ~8–10 рабочих дней**
