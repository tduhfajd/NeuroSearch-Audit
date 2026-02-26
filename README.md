# NeuroSearch Audit

Локальный инструмент для SEO-аудита и AI-ready оценки сайтов.

## Foundation Local Runbook

### 1) Основной путь: PostgreSQL через Homebrew

```bash
brew install postgresql@16
brew services start postgresql@16
```

Проверка состояния сервиса:

```bash
brew services list | rg postgresql@16
```

### 2) Fallback: PostgreSQL через Docker Compose

```bash
docker compose up -d db
```

Остановка fallback-инфраструктуры:

```bash
docker compose down
```

### 3) Подготовка окружения

```bash
cp .env.example .env
```

### 4) Применение миграций Alembic

```bash
alembic -c backend/db/migrations/alembic.ini upgrade head
```

Проверка текущей ревизии:

```bash
alembic -c backend/db/migrations/alembic.ini current
```

### 5) Запуск API

```bash
uvicorn backend.main:app --reload --port 8000
```

### 6) Базовая проверка API

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/health/db
```
