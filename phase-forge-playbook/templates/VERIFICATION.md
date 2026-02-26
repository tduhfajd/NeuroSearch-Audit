---
phase: X
status: pass | fail
verified: YYYY-MM-DD
---

# Phase X: [Название] — Verification Report

## Observable Truths

Из Success Criteria фазы. Каждый критерий проверен фактически.

| # | Truth | Verified | Evidence |
|---|-------|----------|----------|
| 1 | [Критерий из Success Criteria] | ✅ / ❌ | [Как проверено] |
| 2 | [Критерий из Success Criteria] | ✅ / ❌ | [Как проверено] |
| 3 | [Критерий из Success Criteria] | ✅ / ❌ | [Как проверено] |

**Result:** [X]/[Y] truths verified

## Required Artifacts

Ожидаемые файлы существуют и содержат реальную реализацию.

| File | Exists | Substantive | Wired |
|------|--------|-------------|-------|
| [path/to/file] | ✅ / ❌ | ✅ / ❌ | ✅ / ❌ |
| [path/to/file] | ✅ / ❌ | ✅ / ❌ | ✅ / ❌ |

**Stub check:** [Нет стабов / Обнаружены стабы: список]

## Key Wiring

Компоненты подключены друг к другу.

| Connection | Status | Evidence |
|------------|--------|----------|
| [Компонент → API] | ✅ / ❌ | [Как проверено] |
| [API → Database] | ✅ / ❌ | [Как проверено] |
| [Form → Handler] | ✅ / ❌ | [Как проверено] |

## Requirements Coverage

| Requirement | Phase Goal | Status |
|-------------|-----------|--------|
| [REQ-ID] | [Связанный критерий] | ✅ Complete / ❌ Missing |

## Gaps

[Если нет: "Нет gaps — все проверки пройдены"]

- [Описание gap 1]
- [Описание gap 2]

## Verdict

**[PASS / FAIL]**

[Обоснование. Если FAIL — рекомендуемые действия.]
