# NeuroSearch Audit

Локальный инструмент для SEO-аудита и AI-ready оценки сайтов: crawl -> analyze -> ai-analyze -> PDF report.

## Prerequisites

- macOS (Apple Silicon), Python 3.12
- PostgreSQL 16
- Playwright Chromium
- Опционально: Redis/RQ для фоновой очереди (в v1 используется in-memory queue)

## Install And Run

### 1) Prepare environment

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
playwright install chromium
```

### 2) Start PostgreSQL

Основной путь (Homebrew):

```bash
brew install postgresql@16
brew services start postgresql@16
```

Fallback (Docker Compose):

```bash
docker compose up -d db
```

### 3) Run migrations

```bash
alembic -c backend/db/migrations/alembic.ini upgrade head
```

### 4) Setup AI session and validate health

```bash
python -m backend.analyzer.ai_bridge --setup
python -m backend.analyzer.ai_bridge --health
```

### 5) Start backend

```bash
uvicorn backend.main:app --reload --port 8000
```

## First Audit Flow

### 1) Create audit

```bash
curl -s -X POST http://127.0.0.1:8000/audits \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://example.com",
    "client_name": "ООО Пример",
    "niche": "B2B SaaS",
    "region": "Москва",
    "goal": "leads",
    "crawl_depth": 200
  }'
```

### 2) Poll status

```bash
curl -s http://127.0.0.1:8000/audits/<AUDIT_ID>/status
```

### 3) Run rule-based analysis and AI analysis

```bash
curl -s -X POST http://127.0.0.1:8000/audits/<AUDIT_ID>/analyze
curl -s -X POST http://127.0.0.1:8000/audits/<AUDIT_ID>/ai-analyze
```

### 4) Download report and KP

```bash
curl -L -o report.pdf http://127.0.0.1:8000/audits/<AUDIT_ID>/report/pdf
curl -L -o kp.pdf http://127.0.0.1:8000/audits/<AUDIT_ID>/report/kp
```

## Known Limits

- ChatGPT Plus rate limit: при перегрузке этап AI может перейти в partial mode.
- Session state обязательна: при истечении сессии API вернет `reauth_required`.
- JS-heavy страницы: применяется timeout fallback policy и ограниченный retry budget.

## Operational Invariants

- Любая диагностируемая ошибка пайплайна возвращается в контракте `code/message/retryable`.
- Повторный аудит одного домена создает отдельный `audit_id` и отдельные report artifacts.
- Этап AI не должен валить весь запуск при исчерпании rate-limit retries; допустим partial result.

## Troubleshooting

### `reauth_required`

1. Выполните повторно setup:
   `python -m backend.analyzer.ai_bridge --setup`
2. Проверьте состояние:
   `python -m backend.analyzer.ai_bridge --health`

### `rate_limit`

1. Подождите окно лимитов ChatGPT Plus.
2. Перезапустите только AI-этап:
   `POST /audits/<AUDIT_ID>/ai-analyze`

### `persistence_error`

1. Проверьте доступность БД и права записи в каталог отчетов.
2. Перезапустите генерацию отчета:
   `GET /audits/<AUDIT_ID>/report/pdf`

### Crawl timeouts on JS-heavy sites

1. Проверьте `audit.meta.spa_diagnostics` и `crawl_errors`.
2. Повторите аудит с меньшей глубиной (`crawl_depth`) для первичной диагностики.

## Recovery Steps

- Если этап crawl упал: создайте новый аудит и повторите запуск.
- Если упал только ai/report: используйте существующий `audit_id` и перезапустите нужный endpoint.
- Если нужна чистая среда: остановите backend, проверьте БД, примените миграции и перезапустите сервис.
