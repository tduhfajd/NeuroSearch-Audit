# NeuroSearch Audit

## What This Is

Локальный внутренний инструмент на Mac (Apple Silicon), который автоматизирует SEO-аудит сайтов с оценкой готовности к AI-ответам. Краулит сайт, анализирует техническое здоровье и AI-видимость по правилам + через ChatGPT Plus (без API, через браузерную автоматизацию), и генерирует PDF-отчёт + коммерческое предложение.

Используется для: быстрой квалификации лидов, стандартизации аудита, автоматической генерации КП.

## Core Value

**Аудит сайта → готовый PDF-отчёт с КП за один запуск** — без ручного сбора данных, без API-ключей, на собственном Mac.

## Requirements

### Validated

(Пока нет — необходимо подтверждение)

### Active

- [ ] Краулер: обход сайта до 200 страниц, сбор HTML/мета/ссылок/schema
- [ ] Rule-based анализатор: 20+ проверок (индексация, дубли, мета, canonical, schema)
- [ ] AI-анализ: оценка топ-10 страниц через ChatGPT Plus (Playwright)
- [ ] Скоринг: SEO Score + AI Visibility Readiness Index (5 метрик)
- [ ] Карта проблем: P0/P1/P2/P3 с описанием и рекомендациями
- [ ] Дашборд: список аудитов, метрики, статус
- [ ] PDF-отчёт: цифры из анализатора + текст от ChatGPT
- [ ] Генератор КП: 3 пакета (Start / Growth / Authority)

### Out of Scope

- SaaS / облачный деплой — внутренний инструмент, не продукт
- Мониторинг SERP позиций — не входит в MVP, слишком сложно и ненадёжно
- Гарантии попадания в AI-ответы — невозможно обещать, честная метрика "вероятность"
- Интеграция с Яндекс.Вебмастер / Google Search Console API — v3 задел
- Мобильное приложение — только десктоп Mac

## Context

- Рынок: РФ (Яндекс приоритет) + Google
- AI-выдача: Яндекс Нейро, ChatGPT с web retrieval, GigaChat
- Платформа: macOS Apple Silicon (M1/M2/M3/M4), нативный arm64
- AI-движок: ChatGPT Plus через Playwright (без API) — основной; Ollama — резервный
- Стек: Python 3.12 + FastAPI + Scrapy + PostgreSQL + WeasyPrint
- Единственный пользователь: сам владелец (не команда)

## Constraints

- **Platform**: macOS Apple Silicon only — нет смысла поддерживать Linux/Windows для внутреннего инструмента
- **AI Access**: ChatGPT Plus через браузер — нет API-ключа, использование Playwright; rate limit ~50 сообщений/3ч
- **No deploy**: только локально на localhost — нет инфраструктуры, нет хостинга
- **Budget**: нулевые recurring costs — только подписка ChatGPT Plus уже есть
- **Timeline**: MVP за 8–10 рабочих дней
- **Solo developer**: один разработчик, нет команды

## Key Decisions

| Решение | Обоснование | Результат |
|---------|-------------|-----------|
| Python + FastAPI вместо Node.js | Scrapy + Playwright лучше на Python; WeasyPrint — Python-only | ✓ Good |
| ChatGPT Playwright вместо API | Нет API-ключа, есть Plus подписка | ✓ Good |
| PostgreSQL вместо SQLite | Возможность v2 расширения, нормальный SQL | ✓ Good |
| HTML+Tailwind+Alpine.js вместо Next.js | Нет сборки, нет Node.js процесса, достаточно для single-user | ✓ Good |
| uv вместо pip/poetry | Нативный arm64, самый быстрый пакетный менеджер | ✓ Good |
| Google PageSpeed API вместо Lighthouse CLI | 2–3 сек/запрос vs 30–60 сек, стабильные данные, бесплатный ключ | ✓ Good |
| Один профиль + поле `client_name` в `audits` | Мультитенантность не нужна для single-user; `client_name` даёт фильтрацию | ✓ Good |
| Фиксированные пакеты КП в v1 | Формула по числу страниц требует накопленных паттернов — v2 | ✓ Good |
| История только локально + Time Machine | S3 избыточен; `pg_dump` в README покрывает риски | ✓ Good |

## ✅ Решения приняты (2026-02-26)

| Вопрос | Решение |
|--------|---------|
| UI-фреймворк | HTML + Tailwind + Alpine.js |
| КП ценообразование | Фиксированные пакеты в v1, формула в v2 |
| PageSpeed | Google PageSpeed API (бесплатный ключ) |
| Клиенты | Один профиль + поле `client_name` в таблице `audits` |
| История аудитов | Только локально, `pg_dump` инструкция в README |
| AI-движок | ChatGPT Playwright основной, Ollama — опциональный резерв |
| Конкуренты в MVP | Только основной сайт; конкуренты — v2 |

---
*Last updated: 2026-02-26 after decisions approved, Phase 1 ready to start*
