# AGENTS.md — NeuroSearch Audit

## Проект

Локальный внутренний инструмент на Mac (Apple Silicon), который автоматизирует SEO-аудит сайтов с оценкой готовности к AI-ответам (Яндекс Нейро, ChatGPT, GigaChat). Краулит сайт, анализирует техническое здоровье и AI-видимость по правилам + через ChatGPT Plus (без API, через Playwright), и генерирует PDF-отчёт + коммерческое предложение.

**Core Value:** Аудит сайта → готовый PDF-отчёт с КП за один запуск — без ручного сбора данных, без API-ключей, на собственном Mac.

**PROJECT.md:** `.planning/PROJECT.md`
**Requirements:** `.planning/REQUIREMENTS.md`
**Roadmap:** `.planning/ROADMAP.md`
**State:** `.planning/STATE.md`

---

## Технологический стек

| Слой | Технологии |
|------|------------|
| Runtime | Python 3.12 (arm64, нативный для Apple Silicon) |
| Backend | FastAPI + Uvicorn (localhost:8000) |
| Crawler | Scrapy 2.x + Playwright (Chromium arm64) |
| AI Bridge | Playwright (Python) → chat.openai.com (ChatGPT Plus) |
| Local AI (opt.) | Ollama (llama3.2) — резервный вариант без сети |
| Database | PostgreSQL 16 (Homebrew local) |
| ORM | SQLAlchemy 2 + Alembic (migrations) |
| Task Queue | Redis + RQ |
| Reports | Jinja2 + WeasyPrint (PDF, кириллица) |
| Frontend | HTML + Tailwind CSS (CDN) + Alpine.js (CDN) |
| Package mgr | uv |
| Linter | ruff |
| Formatter | ruff format |
| Tests | pytest + pytest-asyncio |

---

## Структура репозитория

```
neurosearch-audit/
├── AGENTS.md                        ← этот файл
├── .planning/
│   ├── PROJECT.md
│   ├── REQUIREMENTS.md
│   ├── ROADMAP.md
│   └── STATE.md
├── backend/
│   ├── main.py                      # FastAPI entrypoint, монтирование роутеров
│   ├── config.py                    # Настройки из .env (pydantic-settings)
│   ├── crawler/
│   │   ├── spider.py                # Scrapy spider — обход сайта
│   │   └── playwright_utils.py      # JS-рендеринг страниц
│   ├── analyzer/
│   │   ├── rules.py                 # Rule-based проверки (класс Rule, реестр)
│   │   ├── ai_bridge.py             # Playwright → ChatGPT Plus
│   │   └── scoring.py               # SEO Score, AVRI формулы
│   ├── reports/
│   │   ├── generator.py             # PDF/HTML генерация (WeasyPrint)
│   │   └── templates/               # Jinja2 HTML шаблоны отчётов
│   ├── routers/
│   │   ├── audits.py                # CRUD аудитов
│   │   └── reports.py               # Генерация и выдача PDF
│   └── db/
│       ├── models.py                # SQLAlchemy модели
│       ├── session.py               # DB engine, get_db dependency
│       └── migrations/              # Alembic
│           └── versions/
├── frontend/
│   └── static/
│       └── index.html               # Single-page UI (Tailwind + Alpine.js)
├── chatgpt_session/
│   └── storage_state.json           # Сессия ChatGPT (gitignored!)
├── tests/
│   ├── test_crawler.py
│   ├── test_analyzer.py
│   ├── test_ai_bridge.py
│   └── test_reports.py
├── .env                             # Секреты локально (gitignored!)
├── .env.example                     # Шаблон переменных окружения
├── pyproject.toml                   # Зависимости (uv)
└── README.md
```

---

## API контракт

| Метод | Маршрут | Назначение |
|-------|---------|------------|
| `GET` | `/` | Редирект на `/static/index.html` |
| `GET` | `/health` | Healthcheck: `{"status": "ok"}` |
| `POST` | `/audits` | Создать и запустить новый аудит |
| `GET` | `/audits` | Список всех аудитов |
| `GET` | `/audits/{id}` | Детали аудита: scores, статус |
| `GET` | `/audits/{id}/status` | Статус и прогресс краулинга (polling) |
| `GET` | `/audits/{id}/issues` | Карта проблем, сгруппированных по P0–P3 |
| `POST` | `/audits/{id}/analyze` | Запустить rule-based анализ краулинга |
| `POST` | `/audits/{id}/ai-analyze` | Запустить AI-анализ через ChatGPT |
| `GET` | `/audits/{id}/report/pdf` | Скачать PDF-отчёт |
| `GET` | `/audits/{id}/report/kp` | Скачать КП (PDF) |

### Схема запроса `POST /audits`
```json
{
  "url": "https://example.ru",
  "client_name": "ООО Пример",
  "niche": "B2B SaaS",
  "region": "Москва",
  "goal": "leads",
  "crawl_depth": 200
}
```

### Схема ответа `GET /audits/{id}`
```json
{
  "id": 1,
  "url": "https://example.ru",
  "client_name": "ООО Пример",
  "status": "completed",
  "seo_score": 72,
  "avri_score": 58,
  "pages_crawled": 143,
  "created_at": "2026-02-26T10:00:00Z"
}
```

---

## Модель данных

**Таблица `audits`:**

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `id` | SERIAL | PRIMARY KEY |
| `url` | VARCHAR(512) | NOT NULL |
| `client_name` | VARCHAR(255) | NULLABLE |
| `niche` | VARCHAR(255) | NULLABLE |
| `region` | VARCHAR(100) | NULLABLE |
| `goal` | VARCHAR(50) | NULLABLE (`leads`, `info`, `local`, `b2b`) |
| `crawl_depth` | INTEGER | DEFAULT 200 |
| `status` | VARCHAR(50) | `pending` / `crawling` / `analyzing` / `completed` / `failed` |
| `seo_score` | FLOAT | NULLABLE, 0–100 |
| `avri_score` | FLOAT | NULLABLE, 0–100 |
| `pages_crawled` | INTEGER | DEFAULT 0 |
| `meta` | JSONB | robots/sitemap статус и прочее |
| `created_at` | TIMESTAMP | DEFAULT now() |
| `completed_at` | TIMESTAMP | NULLABLE |

**Таблица `pages`:**

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `id` | SERIAL | PRIMARY KEY |
| `audit_id` | INTEGER | FK → audits.id |
| `url` | VARCHAR(512) | NOT NULL |
| `status_code` | INTEGER | |
| `title` | TEXT | |
| `h1` | TEXT | |
| `meta_description` | TEXT | |
| `canonical` | VARCHAR(512) | |
| `robots_meta` | VARCHAR(100) | |
| `json_ld` | JSONB | массив schema.org блоков |
| `word_count` | INTEGER | |
| `inlinks_count` | INTEGER | |
| `pagespeed_score` | FLOAT | NULLABLE |
| `ai_scores` | JSONB | оценки от ChatGPT (5 метрик + рекомендации) |
| `crawled_at` | TIMESTAMP | DEFAULT now() |

**Таблица `issues`:**

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `id` | SERIAL | PRIMARY KEY |
| `audit_id` | INTEGER | FK → audits.id |
| `page_id` | INTEGER | FK → pages.id, NULLABLE |
| `rule_id` | VARCHAR(20) | напр. `ANA-01` |
| `priority` | VARCHAR(2) | `P0` / `P1` / `P2` / `P3` |
| `title` | VARCHAR(255) | краткое название проблемы |
| `description` | TEXT | детальное описание |
| `recommendation` | TEXT | что сделать |
| `affected_url` | VARCHAR(512) | NULLABLE |

**Таблица `reports`:**

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `id` | SERIAL | PRIMARY KEY |
| `audit_id` | INTEGER | FK → audits.id |
| `type` | VARCHAR(20) | `full_report` / `kp` |
| `file_path` | VARCHAR(512) | путь к PDF на диске |
| `generated_at` | TIMESTAMP | DEFAULT now() |

---

## Правила работы агента

### Разрешено

- Читать файлы, искать по репозиторию, объяснять код.
- Выполнять задачи строго по текущему PLAN.md.
- Делать **минимальный diff** в рамках одной задачи.
- Добавлять/обновлять тесты рядом с изменением.
- Запускать проверки (ruff, pytest) и чинить найденное.
- Обновлять артефакты: `STATE.md`, `SUMMARY.md`, `CHANGELOG.md`.
- Коммитить каждую задачу отдельно (атомарные коммиты).

### Запрещено без явного подтверждения

- Выход за scope текущего плана/фазы.
- Массовые рефакторинги, переименования.
- Изменения схемы БД, auth/security вне спецификации.
- Удаления файлов, `git reset`, разрушительные действия.
- Подключение новых зависимостей без обсуждения.
- Изменение `.env`, конфигурации проекта.
- Любые реальные запросы к ChatGPT/внешним API вне тестовых сценариев.

### Лимиты

- Одна задача из PLAN.md за итерацию.
- Максимум 2 запуска тяжёлых тестов на задачу.
- Тесты падают 2 раза подряд по разным причинам → **остановиться**.

### Stop-policy

Остановись и спроси, если:
- Не хватает требований (неясны инварианты, edge cases).
- Есть риск для данных или безопасности.
- Задача выходит за scope плана.
- Нужна установка пакетов или сетевой вызов.
- Обнаружен баг вне scope → зафиксировать в `.planning/todos/pending/`, не чинить.
- Сессия ChatGPT не работает — не пытаться авторизоваться автоматически.

---

## Workflow выполнения задачи

### Перед началом
1. Прочитать `AGENTS.md` (этот файл).
2. Прочитать `.planning/STATE.md`.
3. Прочитать текущий PLAN.md задачи.

### В ходе выполнения
1. Минимальный diff — только то, что нужно для задачи.
2. Запустить `verify` команды из задачи.
3. Починить linter/test ошибки если нужно.
4. Коммит: `<type>(<phase>-<plan>): <описание>`.

### После выполнения
1. Создать SUMMARY.md для задачи.
2. Обновить `.planning/STATE.md` (позиция, метрики).
3. Обновить `CHANGELOG.md`.
4. Баги вне scope → `.planning/todos/pending/`.

---

## Quality gates

Каждая задача должна пройти перед коммитом:

- [ ] `ruff check backend/` — 0 ошибок
- [ ] `ruff format --check backend/` — 0 diff
- [ ] `pytest tests/ -x -q` — все зелёные (или `xfail`)
- [ ] must_haves из PLAN.md выполнены
- [ ] Нет стабов: `TODO`, `NotImplementedError`, `pass` в production коде
- [ ] Нет секретов в коде (`.env` не закоммичен, `storage_state.json` не закоммичен)

---

## Ключевые соглашения

### Python / FastAPI
- Python 3.12, все типы аннотированы (`from __future__ import annotations` не нужен)
- Импорты: stdlib → third-party → local; разделены пустыми строками
- Модели данных: `pydantic` v2 для request/response схем; `SQLAlchemy` для ORM
- Async: FastAPI endpoints — `async def`; DB queries через `asyncpg` или sync с `run_in_executor`
- Конфигурация: только через `.env` + `pydantic-settings`, никаких хардкодов

### Именование
- Файлы и директории: `snake_case`
- Классы: `PascalCase`
- Переменные, функции: `snake_case`
- Константы: `UPPER_SNAKE_CASE`
- БД поля: `snake_case`
- API маршруты: `/kebab-case` (нет — т.к. FastAPI, использовать `/snake_case`)

### Тесты
- Файл: `tests/test_<модуль>.py`
- Функции: `test_<что_проверяем>_<ожидаемый_результат>()`
- Изоляция: каждый тест не зависит от состояния другого
- БД в тестах: отдельная тестовая БД `neurosearch_test`, rollback после каждого теста
- Playwright в тестах: mock вместо реального браузера (не ходить в ChatGPT в тестах)

### Коммиты
```
<type>(<phase>-<plan>): <краткое описание>
```
Типы: `feat`, `fix`, `test`, `refactor`, `perf`, `chore`, `docs`

Примеры:
```
feat(01-02): добавить SQLAlchemy модели audits/pages/issues/reports
feat(02-01): базовый Scrapy spider с depth limit
fix(04-02): обработка таймаута ответа ChatGPT
test(03-01): тесты для движка rule-based проверок
```

### Безопасность
- Никаких секретов в коде, логах, коммитах
- `.env` и `chatgpt_session/storage_state.json` всегда в `.gitignore`
- Валидация URL на входе (только http/https, нет внутренних адресов)
- При обнаружении уязвимости — зафиксировать, не игнорировать

---

## Что НЕ входит в текущий scope (v1)

- SaaS, облачный деплой, Docker-образ для production
- Мониторинг SERP позиций (Яндекс / Google)
- Анализ конкурентов (только основной сайт в v1)
- Интеграция Google Search Console / Яндекс.Вебмастер API
- Анализ ссылочного профиля (backlinks) — нет внешних API
- Расчёт цен в КП по формуле (только фиксированные пакеты)
- Мобильный интерфейс
- Командная работа / роли / доступы
- Гарантии попадания в AI-ответы (только метрики вероятности)
- Автоматический бэкап / синхронизация (только локально + Time Machine)

---

*AGENTS.md создан: 2026-02-26*
*Текущая фаза: Phase 1 — Foundation (Ready to execute)*
