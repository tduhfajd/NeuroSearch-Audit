# NeuroSearch Audit

Локальный сервис для автоматизированного SEO-аудита сайта и оценки AI-ready (насколько сайт готов к видимости в AI-системах в целом).

## Для чего нужен проект

Сервис закрывает полный цикл в один запуск:

1. Краулит сайт (технический сбор данных по страницам)
2. Считает rule-based метрики и проблемы (P0–P3)
3. Выполняет AI-анализ контента (через AI Bridge, без API-ключа)
4. Генерирует артефакты: PDF-отчёт и КП

Цель: убрать ручной сбор и ручную проверку, чтобы аудит можно было делать быстро и воспроизводимо на локальном Mac.

## Как это работает (архитектура)

- `FastAPI` backend обслуживает API и UI.
- `Crawler` обходит страницы и сохраняет данные в PostgreSQL.
- `Analyzer` запускает rule-based и AI-анализ.
- `Reports` рендерит PDF-отчёт и КП.
- UI (`frontend/static/index.html`) управляет сценариями через API.

Основной flow:

1. `POST /audits` — создать аудит
2. `/audits/{id}/status` — трекать прогресс
3. `POST /audits/{id}/analyze` — rule-based анализ
4. `POST /audits/{id}/ai-analyze` — AI-анализ
5. `GET /audits/{id}/report/pdf` и `/report/kp` — скачать документы

## Быстрый старт для macOS Apple Silicon (M1/M2/M3/M4)

Ниже — максимально дружелюбный сценарий установки “с нуля”.

### Самый простой путь для обычного пользователя

1. Выполнить bootstrap: `./scripts/bootstrap_macos_arm64.sh`
2. Запустить сервис: `./scripts/run_local.sh`
3. Открыть UI и завершить настройку в интерфейсе (`Настройки`)

### Вариант A (рекомендуется): one-command bootstrap

```bash
chmod +x scripts/bootstrap_macos_arm64.sh scripts/run_local.sh
./scripts/bootstrap_macos_arm64.sh
```

Скрипт автоматически:

- проверит, что у вас macOS arm64
- проверит/установит Xcode CLT и Homebrew
- установит `python@3.12` и `postgresql@16`
- поднимет `postgresql@16` через `brew services`
- создаст роль/БД (`user` / `neurosearch_audit`) при отсутствии
- создаст `.env` из `.env.example`
- создаст `.venv` и установит Python-зависимости
- установит Playwright Chromium
- применит Alembic миграции

После установки запуск backend:

```bash
./scripts/run_local.sh
```

UI:

- http://127.0.0.1:8000/
- http://127.0.0.1:8000/static/index.html

После запуска зайдите во вкладку `Настройки`:

1. Сохраните `Google PageSpeed API Key` один раз (глобально)
2. Нажмите `Запустить авторизацию` в блоке AI Bridge и войдите в ChatGPT в открывшемся браузере

### Вариант B: Docker

```bash
docker compose up -d --build
```

UI:

- http://127.0.0.1:8000/static/index.html

## Настройка AI Bridge (обязательно для AI-анализа)

AI-анализ работает через AI Bridge и локальную сессию ChatGPT Plus (`storage_state.json`).
ChatGPT используется как инструмент оценки, а не как целевая система оптимизации.

Один раз выполните:

```bash
.venv/bin/python -m backend.analyzer.ai_bridge --setup
.venv/bin/python -m backend.analyzer.ai_bridge --health
```

Если используете Docker, дополнительно проверьте внутри контейнера:

```bash
docker compose exec app python -m backend.analyzer.ai_bridge --health
```

Важно для Docker:

- Кнопка `Запустить авторизацию` в UI не может открыть видимое окно браузера внутри контейнера (нет X server/GUI).
- Для Docker-сценария авторизацию ChatGPT нужно делать на Mac-хосте, а не внутри контейнера:

```bash
.venv/bin/python -m backend.analyzer.ai_bridge --setup
```

Файл `chatgpt_session/storage_state.json` примонтирован в контейнер, поэтому после setup на хосте AI-анализ в Docker начинает работать без дополнительных действий.

В UI есть проверка состояния AI Bridge и подсказка по переавторизации.

## Настройка Google PageSpeed API (опционально, но рекомендуется)

По умолчанию сервис использует `Lighthouse` fallback.  
Чтобы включить primary-провайдер (`Google PageSpeed API`), нужен API key.

Как получить ключ:

1. Откройте Google Cloud Console: `https://console.cloud.google.com/`
2. Создайте проект (или выберите существующий) в селекторе проектов.
3. Перейдите в `APIs & Services -> Library`.
4. Найдите `PageSpeed Insights API` и нажмите `Enable`.
5. Перейдите в `APIs & Services -> Credentials`.
6. Нажмите `Create credentials -> API key`.
7. В форме `Create API key` заполните:
   - `Name`: любое понятное имя, например `NeuroSearch Dashboard`
   - `Authenticate API calls through a service account`: не включать
   - `Application restrictions`: `None` (для локального запуска на Mac)
   - `API restrictions`: `Restrict key` -> выбрать только `PageSpeed Insights API`
8. Нажмите `Create`, затем скопируйте сгенерированный ключ.

Как передать ключ в сервис:

1. Через UI `Настройки` (рекомендуется): сохранить один глобальный ключ.
   - Откройте `http://127.0.0.1:8000/static/index.html`
   - Перейдите в раздел `Настройки`
   - Вставьте ключ в поле `Google PageSpeed API Key`
   - Нажмите `Сохранить`
2. Через UI `Новый аудит`: указать ключ только для конкретного запуска.
3. Через `.env` (глобально для всех аудитов):

```env
PAGESPEED_API_KEY=ваш_ключ
```

Приоритет такой:

- ключ из формы создания аудита (если указан)
- ключ из UI `Настройки` (если сохранён)
- иначе `PAGESPEED_API_KEY` из `.env`
- иначе fallback на `Lighthouse`

## Минимальная проверка после запуска

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/health/db
curl -s http://127.0.0.1:8000/ai-bridge/health
```

Ожидаемо:

- `health` -> `{"status":"ok"}`
- `health/db` -> `{"status":"ok"}`
- `ai-bridge/health` -> `ok` или `reauth_required`

## Troubleshooting

### `reauth_required`

Повторно выполните:

```bash
.venv/bin/python -m backend.analyzer.ai_bridge --setup
.venv/bin/python -m backend.analyzer.ai_bridge --health
```

### `rate_limit`

Подождите окно лимитов AI Bridge/провайдера и повторите:

```bash
POST /audits/<AUDIT_ID>/ai-analyze
```

### Backend не стартует

Проверьте:

- работает ли PostgreSQL (`brew services list`)
- корректен ли `DATABASE_URL` в `.env`
- применены ли миграции

## Полезные команды

```bash
# Локальный запуск
./scripts/run_local.sh

# Миграции
.venv/bin/alembic -c backend/db/migrations/alembic.ini upgrade head

# Тесты
pytest -q

# Линтер/формат
ruff check backend tests
ruff format --check backend tests
```
