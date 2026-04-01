# Quality Gates

## Gate Strategy
Каждый аудит проходит обязательные проверки до передачи во внешний AI и перед выдачей финального пакета документов.

## G-001 Crawl Completeness Gate
- Проверка: есть минимально допустимый охват ключевых разделов сайта.
- Fail Condition: обнаружена критическая неполнота обхода.
- Action: повторный crawl с расширенными стратегиями discovery.

## G-002 Data Contract Gate
- Проверка: все обязательные JSON-файлы существуют и валидны по schema version.
- Fail Condition: отсутствует файл или нарушен контракт.
- Action: блокировка package, повтор этапа package builder.

## G-003 Evidence Coverage Gate
- Проверка: high/medium findings имеют evidence ссылку.
- Fail Condition: finding без URL/факта/source.
- Action: отклонение findings/recommendations до исправления.

## G-004 Contradiction Integrity Gate
- Проверка: contradictions имеют минимум два независимых источника.
- Fail Condition: contradiction на неполной доказательной базе.
- Action: downgrade severity или маркировка “requires verification”.

## G-005 Scoring Reproducibility Gate
- Проверка: повторный расчет score на тех же данных дает одинаковый результат.
- Fail Condition: расхождение выше допустимого порога.
- Action: блокировка публикации score, расследование версии ruleset.

## G-006 Prompt Compliance Gate
- Проверка: каждый промт содержит role/audience/inputs/structure/evidence/no-fabrication.
- Fail Condition: пропущен обязательный раздел.
- Action: regenerate prompts.

## G-007 Final Package Gate
- Проверка: manifest корректен, набор файлов полный, статусы этапов complete.
- Fail Condition: package неполный или несогласованный.
- Action: возврат на этап package assembly.

## Operational Metrics
- Доля аудитов, прошедших все gates с первого раза.
- Среднее время прохождения gates.
- Доля findings без evidence (целевое значение: 0 для high severity).
- Доля пересборок package.

## Facts
- `idea.md` акцентирует anti-hallucination, evidence-first и детерминированность.

## Assumptions
- Quality gates применяются до генерации финальных клиентских документов.

## Hypotheses
- Ранние gate-проверки снизят количество ручных правок отчетов и КП.

## Open Questions
- Какой максимальный процент допускается для flagged low-confidence findings в MVP.

## Traceability
- `idea.md`: секции про “не выдумывать”, обязательные ссылки на факты, роли contradictions и детерминированный core.
