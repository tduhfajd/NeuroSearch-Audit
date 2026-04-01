# Technology Stack

## Stack Goal
Зафиксировать согласованный технологический стек для реализации NeuroSearch, чтобы команда разработки и пресейла опиралась на единый инженерный baseline.

## Decision
Принять гибридный стек `Go + Python` с разделением ролей.

## Selected Stack (MVP-1)
- Core Crawler: `Go`.
- Technical Parsing: `Go`.
- Semantic Parsing / LLM-ready extraction: `Python`.
- JS Rendering Layer: изолированный `Playwright`-совместимый browser renderer.
- Storage: `PostgreSQL`.
- Queue/Broker: `Redis Streams`.

## Selected Stack (MVP-2)
- Core Crawler: `Go`.
- Semantic/NLP workers: `Python`.
- Storage: `PostgreSQL` + `ClickHouse` (для аналитики и отчетных агрегаций).
- Queue/Broker: `Redis Streams` или переход на `RabbitMQ` при росте нагрузки.

## Module-to-Stack Mapping
- M-03 Crawler: `Go`.
- M-05 Technical Parser: `Go`.
- M-06 Semantic Parser: `Python`.
- M-07 Entity Builder: `Python` (rule-based extraction), возможен частичный перенос в `Go` для hot paths.
- M-08/M-09/M-10 (coverage/contradictions/scoring): `Python`.
- M-12 Prompt Generator: `Python`.
- M-13 Package Builder: `Go` или `Python` (в MVP допускается реализация в любом слое с единым контрактом).

## Why This Stack
- `Go` даёт устойчивую и экономичную конкурентность для IO-нагруженного crawl-ядра.
- `Python` ускоряет развитие семантических правил и итерации над анализом контента.
- Разделение слоев снижает риск, что нестабильность рендеринга/семантики повлияет на core crawler.
- `PostgreSQL` закрывает роль source-of-truth для артефактов аудита.
- `ClickHouse` добавляется только когда нужна дешевая аналитика больших объемов.

## Alternatives

### A-01 Python-only
- Плюсы: один язык и быстрее найм/онбординг.
- Минусы: слабее предсказуемость и эффективность на высоконагруженном crawl-core.

### A-02 Rust-only
- Плюсы: максимальная производительность и контроль ресурсов.
- Минусы: выше стоимость разработки и ниже скорость итераций для семантического слоя.

### A-03 Go-only
- Плюсы: простота эксплуатации одного runtime.
- Минусы: медленнее эксперименты в NLP/семантическом извлечении.

## Constraints
- Любой модуль обязан сохранять совместимость с утвержденными JSON-контрактами.
- Смена технологии в модуле допускается только без нарушения schema compatibility.

## Facts
- В `idea.md` явно предложен стек: Go для core crawler, Python для semantic layer, PostgreSQL, Redis Streams (MVP), ClickHouse/RabbitMQ на росте.

## Assumptions
- Команда имеет компетенции в Go и Python.
- Для MVP-1 достаточно `Redis Streams` без немедленного перехода на RabbitMQ.

## Hypotheses
- Гибридный стек даст лучший баланс time-to-market и эксплуатационной устойчивости, чем mono-language подход.

## Open Questions
- На каком этапе фиксировать переход с Redis Streams на RabbitMQ.
- Нужен ли отдельный сервис нормализации RU-геоданных в MVP-1 или MVP-2.

## Traceability
- `idea.md`: секции “Дополнение к ТЗ: технологический стек Smart Crawler”, “MVP+”, сравнение Python-only/Rust-only/Go+Python и рекомендации по Storage/Queue.
