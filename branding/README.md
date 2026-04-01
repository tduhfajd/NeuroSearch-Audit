# Branding

Здесь лежат шаблоны и пользовательские конфиги бренда для клиентских отчетов.

Самый простой способ создать свою папку бренда:

```bash
make brand-example
```

Или:

```bash
python create_branding_bundle.py
```

Если хотите, чтобы скрипт сразу спросил название компании, email, телефон и реквизиты:

```bash
make brand-example-interactive
```

Или:

```bash
python create_branding_bundle.py --interactive
```

По умолчанию будет создана папка:

```text
branding/my-brand/
```

Внутри нее будут:
- `brand.yml`
- `logo.png`

Дальше:
1. Отредактируйте `branding/my-brand/brand.yml`
2. Замените `branding/my-brand/logo.png` своим логотипом
3. Запустите аудит:

```bash
python run_audit.py https://example.com --brand branding/my-brand/brand.yml
```
