# NeuroSearch Analyzer

<p align="center">
  <strong>Локальная система аудита сайтов с готовыми клиентскими отчетами</strong><br/>
  SEO · GEO · AEO · AIO · LEO
</p>

<p align="center">
  <a href="examples/kuklapups/report_kuklapups.ru.pdf">Демо PDF</a> ·
  <a href="examples/kuklapups/report_kuklapups.ru.html">Демо HTML</a> ·
  <a href="examples/kuklapups/internal_technical_report.md">Тех. отчет</a> ·
  <a href="#самый-короткий-путь">Быстрый старт</a>
</p>

## Содержание

- [О проекте](#о-проекте)
- [Примеры готовых отчетов](#примеры-готовых-отчетов)
- [Что делает система](#что-делает-система)
- [Что нужно установить](#что-нужно-установить)
- [Самый короткий путь](#самый-короткий-путь)
- [Быстрый запуск: одна команда](#быстрый-запуск-одна-команда)
- [Пользовательский брендинг отчетов](#пользовательский-брендинг-отчетов)
- [Что получится после запуска](#что-получится-после-запуска)
- [Очистка сгенерированных файлов](#очистка-сгенерированных-файлов)
- [Если что-то не работает](#если-что-то-не-работает)
- [Автор](#автор)

## О проекте

NeuroSearch Analyzer это локальная система аудита сайтов. Она обходит сайт, собирает технические и контентные сигналы, выделяет смысловые блоки и факты, считает индексы готовности к SEO, GEO, AEO, AIO и LEO, а затем собирает готовый пакет артефактов и клиентский отчет.

Система предназначена для:
- владельцев агентств и пресейл-команд;
- SEO-, GEO-, AEO- и AI-специалистов;
- технических лидов и разработчиков;
- аналитиков, которым нужен воспроизводимый аудит сайта без ручной сборки данных.

## Примеры готовых отчетов

Ниже лежит реальный демонстрационный набор, собранный системой для сайта `kuklapups.ru`.

Клиентские отчеты:
- [PDF-отчет](examples/kuklapups/report_kuklapups.ru.pdf)
- [HTML-отчет](examples/kuklapups/report_kuklapups.ru.html)
- [DOCX-отчет](examples/kuklapups/report_kuklapups.ru.docx)
- [Markdown-версия клиентского отчета](examples/kuklapups/report_kuklapups.ru.md)

Технические и внутренние документы:
- [Внутренний технический отчет](examples/kuklapups/internal_technical_report.md)
- [Технический отчет для клиента](examples/kuklapups/technical_client_report.md)
- [Технический план работ](examples/kuklapups/technical_action_plan.md)
- [Коммерческое предложение](examples/kuklapups/commercial_offer.md)

## Что делает система

После запуска NeuroSearch Analyzer:
- обходит сайт и сохраняет карту страниц;
- извлекает технические сигналы: заголовки, мета-теги, каноникал, ссылки, структуру страниц;
- определяет смысловые блоки и сущности;
- находит пробелы и противоречия в данных сайта;
- рассчитывает индексы и рекомендации;
- формирует готовые отчеты в `PDF`, `HTML`, `DOCX` и `Markdown`;
- создает отдельный внутренний технический отчет в `Markdown` для команды внедрения.

Главный результат для пользователя это готовый отчет по сайту и полный пакет артефактов, на котором этот отчет основан.

## Что нужно установить

Для полной работы на компьютере должны быть установлены:
- `Git`
- `Go`
- `Python 3`
- `Node.js`
- `Pandoc`
- `LaTeX`-движок для сборки PDF
- браузер `Chromium` для Playwright

Ниже приведен подробный порядок установки.

## Установка на macOS

### 1. Установите Homebrew

Если Homebrew еще не установлен:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Установите системные зависимости

```bash
brew install git go python node pandoc --cask mactex-no-gui
```

Если `mactex-no-gui` не устанавливается, используйте:

```bash
brew install --cask mactex
```

### 3. Скачайте проект

```bash
git clone <URL-ВАШЕГО-РЕПОЗИТОРИЯ>
cd NeuroSearch-Audit
```

### 4. Создайте Python-окружение

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Установите Node.js зависимости

```bash
npm install
```

### 6. Установите браузер для Playwright

```bash
npx playwright install chromium
```

### 7. Проверьте, что все доступно

```bash
go version
python --version
node --version
npx playwright --version
pandoc --version
```

Если LaTeX установлен правильно, команда ниже должна вернуть путь к движку:

```bash
which lualatex
```

## Установка на Ubuntu / Debian Linux

### 1. Обновите список пакетов

```bash
sudo apt update
```

### 2. Установите системные зависимости

```bash
sudo apt install -y git golang python3 python3-venv python3-pip nodejs npm pandoc texlive-latex-base texlive-latex-recommended texlive-fonts-recommended lmodern
```

### 3. Скачайте проект

```bash
git clone <URL-ВАШЕГО-РЕПОЗИТОРИЯ>
cd NeuroSearch-Audit
```

### 4. Создайте Python-окружение

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Установите Node.js зависимости

```bash
npm install
```

### 6. Установите Chromium для Playwright

```bash
npx playwright install chromium
```

### 7. Проверьте установку

```bash
go version
python --version
node --version
pandoc --version
which lualatex
```

## Быстрая установка на Windows

Для Windows есть отдельный установщик:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup_windows.ps1
```

После установки:

```powershell
.\.venv\Scripts\activate
python run_audit.py https://example.com
```

## Самый короткий путь

### macOS / Linux

```bash
chmod +x setup_local.sh
./setup_local.sh
source .venv/bin/activate
python run_audit.py https://example.com
```

Либо через `make`:

```bash
make setup
source .venv/bin/activate
make check
make audit URL=https://example.com
```

### Windows

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup_windows.ps1
.\.venv\Scripts\activate
python run_audit.py https://example.com
```

## Установка на Windows

Проще всего ставить зависимости через `winget`.

### 1. Установите системные зависимости

Откройте PowerShell от имени пользователя и выполните:

```powershell
winget install --id Git.Git -e
winget install --id GoLang.Go -e
winget install --id Python.Python.3.11 -e
winget install --id OpenJS.NodeJS.LTS -e
winget install --id JohnMacFarlane.Pandoc -e
winget install --id MiKTeX.MiKTeX -e
```

После установки MiKTeX откройте его консоль и разрешите автоматическую установку недостающих пакетов.

### 2. Скачайте проект

```powershell
git clone <URL-ВАШЕГО-РЕПОЗИТОРИЯ>
cd NeuroSearch-Audit
```

### 3. Создайте Python-окружение

```powershell
py -3 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Установите Node.js зависимости

```powershell
npm install
```

### 5. Установите Chromium для Playwright

```powershell
npx playwright install chromium
```

### 6. Проверьте установку

```powershell
go version
python --version
node --version
pandoc --version
```

## Быстрая установка: одна команда

Если вы используете macOS или Ubuntu / Debian Linux, можно выполнить почти всю установку одной командой:

```bash
chmod +x setup_local.sh
./setup_local.sh
```

Скрипт:
- проверит и установит системные зависимости;
- создаст `.venv`;
- установит Python-пакеты из `requirements.txt`;
- установит Node.js зависимости;
- скачает `Chromium` для Playwright.

После этого останется только активировать окружение и запустить аудит.

```bash
source .venv/bin/activate
python run_audit.py https://example.com
```

## Проверка установки

После установки удобно сразу проверить, что все готово к работе.

### macOS / Linux

```bash
source .venv/bin/activate
python run_audit.py --help
go version
python --version
node --version
pandoc --version
```

### Windows

```powershell
.\.venv\Scripts\activate
python run_audit.py --help
go version
python --version
node --version
pandoc --version
```

Если команда `python run_audit.py --help` отрабатывает без ошибок, значит пользовательский вход настроен правильно.

## Команды через Makefile

Для macOS и Linux можно использовать короткие команды:

```bash
make help
make setup
make check
make audit URL=https://example.com
make brand-example-interactive
make brand-example
make clean-generated
```

Что делают команды:
- `make setup` запускает локальный установщик;
- `make check` проверяет, что основные зависимости доступны;
- `make audit URL=https://example.com` запускает аудит сайта.
- `make brand-example-interactive` создает папку бренда и сразу спрашивает данные компании.
- `make brand-example` создает готовую папку `branding/my-brand` для вашего бренда.
- `make clean-generated` удаляет все сгенерированные артефакты запусков.

## Быстрый запуск: одна команда

После установки всех зависимостей пользователю достаточно ввести одну команду и адрес сайта.

### macOS / Linux

Если активировано виртуальное окружение:

```bash
python run_audit.py https://example.com
```

Если нужен свой фирменный стиль:

```bash
python run_audit.py https://example.com --brand branding/my-brand/brand.yml
```

Если вы не активировали окружение, используйте полный путь к Python из `.venv`.

Пример:

```bash
.venv/bin/python run_audit.py https://example.com
```

### Windows

Если виртуальное окружение активировано:

```powershell
python run_audit.py https://example.com
```

Либо:

```powershell
py run_audit.py https://example.com
```

Если нужен свой фирменный стиль:

```powershell
python run_audit.py https://example.com --brand branding\my-brand\brand.yml
```

Скрипт сам запустит полный аудит и после завершения покажет пути к готовым отчетам.

## Пользовательский брендинг отчетов

Система поддерживает свой логотип и реквизиты компании для клиентских отчетов.

Как это работает:
- вы создаете свой `brand.yml`
- кладете рядом свой логотип в `PNG`
- запускаете аудит с параметром `--brand`

Готовый пример лежит здесь:
- [branding/README.md](branding/README.md)
- [branding/example/brand.yml](branding/example/brand.yml)

Самый простой сценарий:

### 1. Создать свою папку бренда

```bash
make brand-example
```

Или:

```bash
python create_branding_bundle.py
```

Если хотите сразу ввести название компании, email, телефон и реквизиты в интерактивном режиме:

```bash
make brand-example-interactive
```

Или:

```bash
python create_branding_bundle.py --interactive
```

После этого появится папка:

```text
branding/my-brand/
```

### 2. Положить свой логотип

Путь по умолчанию:

```text
branding/my-brand/logo.png
```

Если вы хотите использовать другое имя файла, поменяйте поле `logo` в `branding/my-brand/brand.yml`.

### 3. Отредактировать `brand.yml`

Пример:

```yaml
name: "Мой Бренд"
logo: "logo.png"

colors:
  primary: "#1F4ED8"
  secondary: "#0F172A"
  accent: "#475569"

company:
  display_name: "Мой Бренд"
  legal_name: "ООО «Мой Бренд»"
  website: "https://example.com"
  email: "hello@example.com"
  phone: "+7 (999) 123-45-67"
  address: "Россия, Москва, Примерная улица, 1"
  requisites:
    - "ИНН 7700000000"
    - "ОГРН 1027700000000"
    - "р/с 40702810000000000000 в АО «Банк»"
    - "БИК 044525000"
```

### 4. Запустить аудит с брендом

```bash
python run_audit.py https://example.com --brand branding/my-brand/brand.yml
```

Что можно задать в `brand.yml`:
- название бренда
- логотип
- основные цвета
- отображаемое название компании
- юридическое название
- сайт
- email
- телефон
- адрес
- список реквизитов

### Требования и рекомендации к PNG-логотипу

Поддерживаемый формат:
- `PNG`

Куда класть файл:
- самый простой вариант: рядом с `brand.yml`
- пример: `branding/my-brand/logo.png`

Как указывать путь:
- в поле `logo` указывается путь относительно самого `brand.yml`
- пример:

```yaml
logo: "logo.png"
```

или:

```yaml
logo: "assets/header.png"
```

Рекомендуемые параметры изображения:
- горизонтальный макет, а не квадрат
- лучше делать именно шапку фирменного бланка, если она у вас есть
- минимальная рекомендуемая ширина: `2000 px`
- комфортная ширина для печатного качества: `2400-3000 px`
- рекомендуемая высота для шапки: `300-900 px`
- фон лучше делать уже таким, каким он должен быть в отчете
- желательно не использовать слишком мелкий текст внутри PNG

Практически:
- хороший безопасный вариант: `2400 x 500 px`
- если это полноценная шапка-бланк: `2480 x 600 px`

Важно:
- логотип или шапка вставляется в начало клиентского отчета на всю ширину страницы
- если PNG слишком высокий, отчет будет выглядеть перегруженно
- для DOCX и HTML лучше всего работает широкий и не слишком высокий баннер

### Где появятся ваши реквизиты

В клиентском отчете сверху будут выведены:
- логотип
- название бренда
- юридическое название
- сайт
- email
- телефон
- адрес
- реквизиты из списка `requisites`

Внутренний технический отчет не брендируется и остается обычным рабочим `Markdown`-документом.

## Что получится после запуска

После успешного запуска в проекте появятся каталоги:
- `audit_package/<audit_id>/` — полный пакет артефактов аудита;
- `runtime/<audit_id>/attempts/001/run_state.json` — состояние выполнения;
- `out/<timestamp>-<domain>/deliverables/client-report/` — готовые отчеты для пользователя.
- `latest_reports/` — два главных отчета в простом месте для быстрого доступа.

Обычно в каталоге `out/.../deliverables/client-report/` будут файлы:
- `report_<domain>.pdf`
- `report_<domain>.html`
- `report_<domain>.docx`
- `report_<domain>.md`

Отдельно внутри пакета аудита создается внутренний технический отчет:
- `audit_package/<audit_id>/exports/internal_technical_report.md`

Для быстрого доступа после каждого запуска обновляется каталог:
- `latest_reports/client_report_<domain>.pdf`
- `latest_reports/client_report_<domain>.html`
- `latest_reports/client_report_<domain>.docx`
- `latest_reports/client_report_<domain>.md`
- `latest_reports/internal_technical_report_<domain>.md`

## Очистка сгенерированных файлов

При активном использовании проект создает новые файлы не только в `out/`, но и в:
- `audit_package/`
- `runtime/`
- `latest_reports/`

Поэтому удаление только `out/` не освобождает все место.

Для полной очистки артефактов запусков используйте:

```bash
python cleanup_generated_artifacts.py --yes
```

Или через `make`:

```bash
make clean-generated
```

Если нужно удалить еще и Python-кэши:

```bash
python cleanup_generated_artifacts.py --include-caches --yes
```

Или:

```bash
make clean-generated-with-caches
```

Эти команды не трогают исходный код, `docs/`, `scripts/`, `testdata/`, `.venv/` и `node_modules/`.

## Самый простой пример

```bash
python run_audit.py https://kuklapups.ru
```

После завершения откройте папку:

```text
out/<timestamp>-kuklapups.ru/deliverables/client-report/
```

Итоговый PDF-отчет будет лежать внутри этой папки.

## Если что-то не работает

### Ошибка `go: command not found`

Значит не установлен Go или он не добавлен в `PATH`.

### Ошибка `python: command not found` или `No module named yaml`

Значит не активировано виртуальное окружение или не выполнена команда:

```bash
pip install -r requirements.txt
```

### Ошибка `pandoc failed`

Значит не установлен `Pandoc` или он не найден в `PATH`.

### Ошибка `No LaTeX engine found`

Значит не установлен LaTeX. Нужен один из движков:
- `lualatex`
- `xelatex`
- `pdflatex`

### Ошибка Playwright / Chromium

Обычно помогает повторная установка браузера:

```bash
npx playwright install chromium
```

## Для кого этот README

Этот README специально упрощен и описывает только:
- что делает система;
- кому она нужна;
- как ее установить на обычный компьютер;
- как запустить аудит одной командой и получить отчет.

Внутренние архитектурные документы, схемы и контракты остаются в папке `docs/`, но для обычного использования они не нужны.

## Автор

**Вадим Евграфов**  
Telegram: [@vadim_evgrafov](https://t.me/vadim_evgrafov)  
Email: [vadim@evgrafov.biz](mailto:vadim@evgrafov.biz)
