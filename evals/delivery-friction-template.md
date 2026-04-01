# Delivery Friction Template

## Use

Заполнять после pilot review и первого handoff по каждому audit.

## Required Inputs

- manual steps after approval
- reformatting steps
- missing exports
- operator complaints
- CRM / task tracker / direct handoff signals

## Command

```text
python3 scripts/capture_delivery_friction.py <audit_package_dir> \
  --manual-steps <n> \
  --reformatting-steps <n> \
  --missing-export <artifact_or_gap> \
  --complaint <boundary_specific_pain> \
  --crm-signal <none|weak|strong> \
  --task-tracker-signal <none|weak|strong> \
  --direct-handoff-signal <none|weak|strong>
```

## Review Questions

1. Какие шаги после approval пришлось делать вручную?
2. Что пришлось переписывать или реформатировать?
3. Какого export artifact не хватило для reviewer или delivery workflow?
4. Повторялась ли эта боль на нескольких audits?
5. Дает ли это прямой сигнал на CRM, task tracker или handoff integration?
