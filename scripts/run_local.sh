#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ ! -x .venv/bin/uvicorn ]]; then
  echo "[run_local] .venv не найден. Сначала выполните: ./scripts/bootstrap_macos_arm64.sh" >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

exec .venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
