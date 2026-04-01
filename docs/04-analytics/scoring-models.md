# Scoring Models

## Scoring Goals
- Сделать приоритизацию прозрачной и воспроизводимой.
- Связать технические и смысловые проблемы с бизнес-ценностью.
- Поддержать KPI для пресейла и delivery.

## S-001 ECS (Entity Coverage Score)
- Назначение: полнота обязательных блоков по сущности.
- Формула: `ECS = sum(weight_i * presence_i) / sum(weight_i)`.
- Диапазон: 0..1.
- Интерпретация:
1. `0.80-1.00`: хорошее покрытие.
2. `0.50-0.79`: среднее, есть существенные gaps.
3. `<0.50`: критически неполное покрытие.

## S-002 CS (Contradiction Score)
- Назначение: интенсивность противоречий.
- Формула: `CS = (3*high + 2*medium + 1*low) / normalization_factor`.
- Интерпретация: чем выше CS, тем выше риск доверия и искажений AI.

## S-003 ARS (AI Readiness Scores)
- Назначение: оценка по 5 направлениям видимости.
- Набор: SEO, GEO, AEO, AIO, LEO.
- Пример принципа расчета:
1. `SEO_score`: tech signals + базовая семантика + structure.
2. `GEO_score`: definition/proof/clarity + низкая конфликтность.
3. `AEO_score`: FAQ/инструкции/короткие ответы/таблицы.
4. `AIO_score`: consistency + entity clarity + structure.
5. `LEO_score`: параметры/сравнения/цены/варианты.

## S-004 LVI (Lead Value Index)
- Назначение: оценить коммерческий потенциал и объем работ.
- Формула (rule-based MVP):
`LVI = w1*P0_gaps + w2*P1_gaps + w3*high_contradictions + w4*complexity_factor`.
- Использование: ранжирование лидов и базовая логика пакетов КП.

## Calibration Policy
- MVP-1: экспертные rule-based веса.
- MVP-2: калибровка по фактическим результатам внедрения.
- Post-MVP: отраслевые профили весов.

## Score Output Requirements
- Для каждого score хранить входные факторы.
- Для каждого score хранить версию ruleset.
- Для high-impact рекомендаций хранить связь со score delta.

## Facts
- В `idea.md` явно указаны ECS, CS, ARS и LVI как центральные метрики.

## Assumptions
- В MVP пороги интерпретации score задаются экспертно и уточняются на пилотах.

## Hypotheses
- Публичная прозрачность формул повысит доверие и упростит продажи.

## Open Questions
- Какие веса ARS подходят для разных отраслей (услуги, e-commerce, B2B).

## Traceability
- `idea.md`: секции “Метрики”, формулы/принципы ECS/CS/ARS/LVI, приоритет на измеримость и продаваемость отчета.
