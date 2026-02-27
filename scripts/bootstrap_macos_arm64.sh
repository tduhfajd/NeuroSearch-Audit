#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

log() {
  printf "\n[bootstrap] %s\n" "$1"
}

fail() {
  printf "\n[bootstrap] ERROR: %s\n" "$1" >&2
  exit 1
}

ensure_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Команда '$1' не найдена"
}

if [[ "$(uname -s)" != "Darwin" ]]; then
  fail "Скрипт поддерживает только macOS"
fi

if [[ "$(uname -m)" != "arm64" ]]; then
  fail "Скрипт предназначен для Apple Silicon (arm64)"
fi

log "Проверяю Xcode Command Line Tools"
if ! xcode-select -p >/dev/null 2>&1; then
  log "Устанавливаю Xcode Command Line Tools"
  xcode-select --install || true
  fail "Завершите установку Xcode Command Line Tools и запустите скрипт снова"
fi

log "Проверяю Homebrew"
if ! command -v brew >/dev/null 2>&1; then
  log "Homebrew не найден. Устанавливаю Homebrew"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# shellcheck disable=SC2016
if [[ -x /opt/homebrew/bin/brew ]]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi
ensure_cmd brew

log "Устанавливаю системные зависимости (python@3.12, postgresql@16)"
brew update
brew install python@3.12 postgresql@16 || true

PY312_BIN="$(brew --prefix python@3.12)/bin/python3.12"
[[ -x "$PY312_BIN" ]] || fail "python3.12 не найден после установки"

PG_PREFIX="$(brew --prefix postgresql@16)"
PSQL_BIN="$PG_PREFIX/bin/psql"
CREATEDB_BIN="$PG_PREFIX/bin/createdb"
[[ -x "$PSQL_BIN" ]] || fail "psql не найден после установки postgresql@16"
[[ -x "$CREATEDB_BIN" ]] || fail "createdb не найден после установки postgresql@16"

log "Запускаю PostgreSQL service"
brew services start postgresql@16 >/dev/null || true

log "Настраиваю локальную БД (role=user, db=neurosearch_audit)"
if ! "$PSQL_BIN" -d postgres -c "SELECT 1" >/dev/null 2>&1; then
  fail "Не удалось подключиться к локальному PostgreSQL. Проверьте brew services"
fi

"$PSQL_BIN" -d postgres <<'SQL'
DO
$$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'user') THEN
    CREATE ROLE "user" LOGIN PASSWORD 'password';
  END IF;
END
$$;
SQL

if ! "$PSQL_BIN" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='neurosearch_audit'" | grep -q 1; then
  "$CREATEDB_BIN" -O user neurosearch_audit
fi

log "Готовлю .env"
if [[ ! -f .env ]]; then
  cp .env.example .env
fi

if ! grep -q '^DATABASE_URL=' .env; then
  printf '\nDATABASE_URL=postgresql+psycopg://user:password@localhost:5432/neurosearch_audit\n' >> .env
fi

if ! grep -q '^AUTO_DRAIN_QUEUE=' .env; then
  printf 'AUTO_DRAIN_QUEUE=true\n' >> .env
fi

log "Создаю venv и устанавливаю python-зависимости"
"$PY312_BIN" -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e .

log "Устанавливаю Playwright Chromium"
.venv/bin/playwright install chromium

log "Применяю миграции БД"
.venv/bin/alembic -c backend/db/migrations/alembic.ini upgrade head

log "Готово"
cat <<'MSG'

Проект установлен.

Следующие шаги:
1) Запуск backend:
   .venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

2) Открыть UI:
   http://127.0.0.1:8000/static/index.html

3) Для AI Bridge (один раз):
   .venv/bin/python -m backend.analyzer.ai_bridge --setup
   .venv/bin/python -m backend.analyzer.ai_bridge --health

MSG
