# Roadmap

## Planning Horizon
- Фаза 0: Foundation.
- Фаза 1: MVP-1 (быстрый пресейл-пакет).
- Фаза 2: MVP-2 (усиление GEO/AEO/LEO).
- Фаза 3: Post-MVP (масштабирование и интеграции).

## Phase 0: Foundation
- Цель: подготовить контракты данных, ruleset версии и базовый runtime.
- Scope:
1. Базовая структура audit package.
2. Версионирование schema/ruleset/prompt pack.
3. Минимальная наблюдаемость и logging.
- Exit Criteria:
1. Все обязательные артефакты пакета валидируются.
2. Есть тестовый end-to-end прогон на демонстрационном сайте.

## Phase 1: MVP-1
- Цель: выдавать продающий и технический пакет документов на основе rule-based анализа.
- Scope:
1. Crawler + parser + page_type.
2. Блоки `definition/process/pricing/faq/proof/terms/contacts/cta`.
3. Сущности `org/service/geo/price/document/faq_question`.
4. Coverage + contradictions.
5. Базовые ARS + LVI.
6. 5 промтов под документы.
- Exit Criteria:
1. По каждому аудиту формируется complete package.
2. Все high severity findings имеют evidence.
3. Внешний AI генерирует 5 документов без ручной дописки фактов.

## Phase 2: MVP-2
- Цель: повысить качество под GEO/AEO/LEO и устойчивость анализа.
- Scope:
1. Усиленный анализ “кратких ответов”, таблиц, сравнений.
2. Более строгая нормализация цен/сроков/гео.
3. Улучшенный LEO scoring для сценариев подбора/сравнения.
4. Репорт дельты относительно baseline.
- Exit Criteria:
1. Рост качества рекомендаций на пилотных кейсах.
2. Снижение ложных contradictions относительно MVP-1.

## Phase 3: Post-MVP
- Цель: операционное масштабирование платформы.
- Scope:
1. Интеграции с CRM/таск-трекерами.
2. Массовая обработка лидов и пакетный режим.
3. Расширение отраслевых ruleset.
4. White-label шаблоны документов.
- Exit Criteria:
1. Поддержка промышленного потока лидов.
2. Стандартизированная передача в sales и delivery.

## Facts
- `idea.md` задает MVP-1 и MVP-2, а также приоритет пакетной генерации документов.

## Assumptions
- Точные календарные сроки будут назначены после ресурсной оценки команды.

## Hypotheses
- Внедрение в фазах снизит риск переработки ruleset и scoring.

## Open Questions
- Какая длительность фаз допустима с учетом целевого окна запуска.

## Traceability
- `idea.md`: секции “MVP-1/MVP-2”, блоки о документах, coverage/contradictions, scoring и Runet-first фокусе.
