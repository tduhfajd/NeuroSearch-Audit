---
status: testing
phase: XX-name
source: [список SUMMARY.md файлов]
started: YYYY-MM-DDTHH:MM:SSZ
updated: YYYY-MM-DDTHH:MM:SSZ
---

# Phase X: [Название] — UAT

## Current Test
<!-- Перезаписывается на каждом тесте — показывает где мы -->

number: 1
name: [название теста]
expected: |
  [что пользователь должен наблюдать]
awaiting: user response

## Tests

### 1. [Название теста]
expected: [наблюдаемое поведение — что пользователь должен увидеть]
result: [pending]

### 2. [Название теста]
expected: [наблюдаемое поведение]
result: [pending]

### 3. [Название теста]
expected: [наблюдаемое поведение]
result: [pending]

## Summary

total: 0
passed: 0
issues: 0
pending: 0
skipped: 0

## Gaps

<!-- YAML формат для потребления plan-phase --gaps -->
<!-- Заполняется при обнаружении issues -->
