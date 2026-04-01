#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_client_report_input import ensure_approved, load_json
from scripts.delivery_i18n import translate_gap, translate_phrase
from scripts.generate_client_report import main as generate_client_report_main


COMMERCIAL_SCHEMA_VERSION = "1.0.0"
TECHNICAL_SCHEMA_VERSION = "2.0.0"

SERVICE_PACKAGES = [
    {
        "id": "PKG-BASE",
        "name": "База: технический фундамент",
        "price": "от 90 000 ₽ за 4 недели",
        "deliverables": [
            "Подробный технический план работ с приоритетами и проверками",
            "Исправление критичных технических и структурных разрывов",
            "Базовый стандарт ключевых страниц и повторный аудит после внедрения",
        ],
        "value": [
            "Снятие главных блокеров роста и повышение управляемости внедрения",
            "Быстрые улучшения на ключевых страницах уже в первые недели",
        ],
    },
    {
        "id": "PKG-GROWTH",
        "name": "Рост: контент, структура и доверие",
        "price": "от 150 000 ₽ за 6 недель",
        "deliverables": [
            "Перестройка ключевых сервисных и коммерческих страниц",
            "Усиление блоков доверия, структуры предложения и конверсионного пути",
            "Контрольный аудит и уточнение следующей волны работ",
        ],
        "value": [
            "Рост понятности предложения для клиента и систем",
            "Сильнее покрывается коммерческий и смешанный спрос",
        ],
    },
    {
        "id": "PKG-SCALE",
        "name": "Системный рост: масштабирование и контроль качества",
        "price": "от 220 000 ₽ за 8 недель",
        "deliverables": [
            "Повторяемый стандарт качества для ключевых шаблонов",
            "План масштабирования на весь приоритетный контур сайта",
            "Контур измерения эффекта и регулярных повторных проверок",
        ],
        "value": [
            "Улучшения становятся системными, а не точечными",
            "Команда получает прозрачный цикл управления качеством сайта",
        ],
    },
]

TASK_LIBRARY = {
    "secure_protocol": {
        "title": "Выравнивание протокола, canonical и HTTPS-контура",
        "problem_statement": "Сайт отдает смешанный протокольный сигнал: в пакете одновременно присутствуют http и https URL.",
        "where_to_change": [
            "Серверные правила редиректа и канонизации",
            "Шаблон `<head>` на ключевых страницах",
            "sitemap.xml и внутренние ссылки на приоритетных шаблонах",
        ],
        "implementation_steps": [
            "Настроить постоянный 301/308-редирект со всех http URL на https-версию.",
            "Проверить и исправить canonical на всех приоритетных страницах так, чтобы он указывал только на https.",
            "Пересобрать sitemap и внутренние ссылки без http-вариантов URL.",
        ],
        "definition_of_done": [
            "Все приоритетные URL открываются только по https.",
            "Canonical, sitemap и внутренние ссылки не содержат http-вариантов.",
        ],
        "expected_effect": "Сайт перестает дробить технические сигналы и получает более устойчивый доверительный контур.",
    },
    "strict_transport_security": {
        "title": "Закрепление безопасного HTTPS-режима через HSTS",
        "problem_statement": "HTTPS-контур сайта не закреплен заголовком Strict-Transport-Security.",
        "where_to_change": [
            "Конфигурация веб-сервера или CDN/балансировщика",
            "Контрольный набор приоритетных https-страниц",
        ],
        "implementation_steps": [
            "Добавить Strict-Transport-Security в HTTPS-ответы с согласованным временем жизни.",
            "Проверить, что все приоритетные URL стабильно отдают HSTS после включения.",
        ],
        "definition_of_done": [
            "На целевых https-страницах присутствует Strict-Transport-Security.",
            "После включения HSTS не появляются регрессии в доступности или контенте.",
        ],
        "expected_effect": "Укрепляет транспортную безопасность и повышает доверие к техническому контуру сайта.",
    },
    "messengers": {
        "title": "Быстрый контактный слой на главной и сервисных страницах",
        "problem_statement": "На ключевых страницах не хватает мгновенного сценария перехода к диалогу через мессенджеры или аналогичный канал.",
        "where_to_change": [
            "Главная страница",
            "Ключевые сервисные страницы и контактный шаблон",
            "Сквозные CTA-блоки и шапка/подвал сайта",
        ],
        "implementation_steps": [
            "Добавить на главную и приоритетные сервисные страницы быстрый канал связи через мессенджер или аналогичный instant-contact сценарий.",
            "Сделать CTA к контакту коротким, повторяемым и заметным на приоритетных шаблонах.",
            "Проверить, что контактный сценарий повторяется и в мобильной версии.",
        ],
        "definition_of_done": [
            "На приоритетных страницах есть видимый быстрый канал связи.",
            "Путь к первому контакту не требует поиска отдельной страницы контактов.",
        ],
        "expected_effect": "Уменьшает потери лидов на первом контакте и ускоряет переход к диалогу.",
    },
    "proof": {
        "title": "Система доказательств компетенции на ключевых страницах",
        "problem_statement": "Сайт недостаточно подтверждает компетенцию компании кейсами, цифрами и другими доказательствами результата.",
        "where_to_change": [
            "Главная страница",
            "Сервисные страницы и страницы услуг",
            "Разделы с кейсами, клиентами, отзывами и портфолио",
        ],
        "implementation_steps": [
            "Добавить кейсы, цифры результата, клиентов, отзывы и иные подтверждения опыта.",
            "Связать proof-блоки с конкретными услугами и CTA, а не держать их изолированно.",
            "Сформировать единый стандарт proof-блоков для повторного использования на ключевых шаблонах.",
        ],
        "definition_of_done": [
            "Главная и ключевые сервисные страницы содержат минимум один сильный proof-блок.",
            "Доказательства привязаны к услугам и понятны без дополнительного контекста.",
        ],
        "expected_effect": "Повышает доверие и снижает сомнения до обращения.",
    },
    "pricing": {
        "title": "Коммерческая ясность и ценовые сигналы",
        "problem_statement": "Приоритетные страницы не до конца раскрывают цену, модель расчета или порог входа.",
        "where_to_change": [
            "Сервисные и коммерческие страницы",
            "CTA-блоки рядом с описанием предложения",
            "Коммерческие секции с условиями и диапазонами стоимости",
        ],
        "implementation_steps": [
            "Добавить диапазоны стоимости, модель расчета или прозрачное объяснение, от чего зависит цена.",
            "Вывести коммерческие условия рядом с ключевыми блоками ценности и CTA.",
        ],
        "definition_of_done": [
            "На целевых страницах есть понятный коммерческий сигнал о стоимости или модели расчета.",
            "Клиент понимает, как перейти от интереса к коммерческому диалогу.",
        ],
        "expected_effect": "Снижает барьер входа и улучшает качество коммерческих лидов.",
    },
    "process_steps": {
        "title": "Пошаговый сценарий работы с клиентом",
        "problem_statement": "Страницы не объясняют по шагам, как происходит работа после обращения.",
        "where_to_change": [
            "Главная страница",
            "Сервисные страницы",
            "FAQ и блоки «как мы работаем»",
        ],
        "implementation_steps": [
            "Добавить блок «этапы работы» на главной и ключевых сервисных страницах.",
            "Привязать этапы к результату, срокам и следующему действию клиента.",
        ],
        "definition_of_done": [
            "На целевых страницах есть понятный сценарий работы от обращения до результата.",
            "Этапы не противоречат CTA и фактическому процессу команды.",
        ],
        "expected_effect": "Снижает неопределенность и делает обращение более понятным для клиента.",
    },
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sync_manifest_documents(package_dir: Path) -> None:
    manifest_path = package_dir / "manifest.json"
    manifest = load_json(manifest_path)
    schema_versions = manifest.setdefault("schema_versions", {})
    schema_versions["commercial_offer"] = COMMERCIAL_SCHEMA_VERSION
    schema_versions["technical_action_plan"] = TECHNICAL_SCHEMA_VERSION
    files = manifest.setdefault("files", [])
    desired = {
        "exports/commercial_offer.json": {
            "path": "exports/commercial_offer.json",
            "category": "export",
            "required": False,
            "schema": "commercial_offer",
            "checksum": sha256_file(package_dir / "exports" / "commercial_offer.json"),
        },
        "exports/technical_action_plan.json": {
            "path": "exports/technical_action_plan.json",
            "category": "export",
            "required": False,
            "schema": "technical_action_plan",
            "checksum": sha256_file(package_dir / "exports" / "technical_action_plan.json"),
        },
    }
    indexed = {entry.get("path"): idx for idx, entry in enumerate(files)}
    for rel, entry in desired.items():
        if rel in indexed:
            files[indexed[rel]] = entry
        else:
            files.append(entry)
    files.sort(key=lambda item: item.get("path", ""))
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def ensure_client_report(package_dir: Path) -> None:
    report_path = package_dir / "exports" / "client_report.json"
    if report_path.exists():
        return
    exit_code = generate_client_report_main(["generate_client_report.py", str(package_dir)])
    if exit_code != 0:
        raise RuntimeError("client report generation failed before commercial document build")


def package_score(package_id: str, top_gaps: list[str]) -> int:
    score = 0
    if package_id == "PKG-BASE":
        for gap in top_gaps:
            if gap in {"secure_protocol", "strict_transport_security", "contacts", "pricing", "process_steps", "proof"}:
                score += 2
    if package_id == "PKG-GROWTH":
        for gap in top_gaps:
            if gap in {"proof", "service_scope", "availability", "faq", "process_steps", "messengers"}:
                score += 2
    if package_id == "PKG-SCALE":
        for gap in top_gaps:
            if gap in {"strict_transport_security", "legal_trust", "mixed_content_safe"}:
                score += 1
    return score


def build_commercial_offer(package_dir: Path) -> dict:
    review_brief = load_json(package_dir / "exports" / "review_brief.json")
    report_input = load_json(package_dir / "exports" / "client_report_input.json")
    top_gaps = [str(item) for item in review_brief.get("top_gaps", [])]
    ranked = sorted(SERVICE_PACKAGES, key=lambda item: package_score(item["id"], top_gaps), reverse=True)
    recommended = ranked[0]["name"] if ranked else SERVICE_PACKAGES[0]["name"]
    crawl_warnings = [translate_phrase(str(item)) for item in review_brief.get("crawl_quality", {}).get("warnings", [])]
    return {
        "schema_version": COMMERCIAL_SCHEMA_VERSION,
        "audit_id": review_brief["audit_id"],
        "package_status": review_brief["package_status"],
        "site": report_input["site"],
        "packages": SERVICE_PACKAGES,
        "recommended_package": recommended,
        "sections": {
            "goal": "Построить поэтапный план работ, который уберет главные ограничения сайта и переведет улучшения в управляемый процесс с понятной проверкой результата.",
            "phases": [
                "Этап 1 (до 7 дней): уточнение зоны внедрения, доступов, владельцев и очередности работ.",
                "Этап 2 (7–30 дней): внедрение технического и контентного фундамента на приоритетных страницах.",
                "Этап 3 (30–90 дней): масштабирование на остальные шаблоны, повторный аудит и корректировка плана.",
            ],
            "client_requirements": [
                "Назначить ответственного за согласование контента и публикацию изменений.",
                "Предоставить технические доступы или контакт команды, которая публикует изменения.",
                "Согласовать цикл обратной связи по макетам, правкам и проверке результата.",
            ],
            "disclaimer": [
                "Мы не обещаем фиксированный бизнес-результат без достаточного горизонта внедрения и проверки изменений на данных.",
                "Работа ведется поэтапно: сначала снимаем главные ограничения, затем масштабируем успешные решения.",
                *crawl_warnings,
            ],
        },
    }


def build_target_pages(review_brief: dict) -> list[str]:
    urls: list[str] = []
    for page in review_brief.get("priority_pages", []):
        url = str(page.get("url") or "").strip()
        if url and url not in urls:
            urls.append(url)
    return urls[:8]


def build_task(gap: str, target_pages: list[str], recommendations: list[dict], index: int) -> dict:
    template = TASK_LIBRARY.get(
        gap,
        {
            "title": translate_gap(gap).capitalize(),
            "problem_statement": f"На приоритетных страницах не хватает блока «{translate_gap(gap)}».",
            "where_to_change": ["Приоритетные коммерческие и сервисные страницы"],
            "implementation_steps": [f"Добавить и стандартизировать блок «{translate_gap(gap)}» на ключевых страницах."],
            "definition_of_done": [f"Блок «{translate_gap(gap)}» добавлен на приоритетные страницы и проверен повторным аудитом."],
            "expected_effect": "Снижается один из критичных разрывов покрытия.",
        },
    )
    rec_steps: list[str] = []
    for recommendation in recommendations:
        for criterion in recommendation.get("acceptance_criteria", []):
            translated = translate_phrase(str(criterion))
            if translated not in rec_steps:
                rec_steps.append(translated)
    implementation_steps = list(template["implementation_steps"])
    if gap in {"secure_protocol", "strict_transport_security"}:
        for step in rec_steps[:5]:
            if step not in implementation_steps:
                implementation_steps.append(step)
    observations = [
        template["problem_statement"],
        f"Задача привязана к gap «{translate_gap(gap)}» из текущего approved package.",
    ]
    return {
        "task_id": f"TASK-{index:02d}",
        "title": template["title"],
        "priority": "P0" if gap in {"secure_protocol", "strict_transport_security"} else "P1",
        "problem_statement": template["problem_statement"],
        "current_observations": observations,
        "where_to_change": list(template["where_to_change"]),
        "target_pages": target_pages,
        "implementation_steps": implementation_steps,
        "definition_of_done": list(template["definition_of_done"]),
        "verification": [
            "Проверить внедрение вручную на целевых URL в браузере.",
            "Повторно прогнать аудит и убедиться, что связанный gap перестал быть приоритетным.",
            "Сверить, что изменения не сломали остальные ключевые страницы и шаблоны.",
        ],
        "expected_effect": template["expected_effect"],
    }


def build_technical_action_plan(package_dir: Path) -> dict:
    review_brief = load_json(package_dir / "exports" / "review_brief.json")
    report_input = load_json(package_dir / "exports" / "client_report_input.json")
    recommendations = load_json(package_dir / "analysis/recommendations.json").get("recommendations", [])
    target_pages = build_target_pages(review_brief)
    top_gaps = [str(item) for item in review_brief.get("top_gaps", [])[:5]]
    tasks = [build_task(gap, target_pages, recommendations, index) for index, gap in enumerate(top_gaps, start=1)]
    if not tasks:
        tasks.append(
            {
                "task_id": "TASK-01",
                "title": "Контрольный повторный аудит",
                "priority": "P2",
                "problem_statement": "Критичные задачи не выявлены, но пакет требует регулярной контрольной проверки.",
                "current_observations": ["На текущем этапе нет новых P0/P1-задач, требующих немедленного внедрения."],
                "where_to_change": ["Ключевые шаблоны и контрольные URL"],
                "target_pages": target_pages,
                "implementation_steps": ["Поддерживать текущий уровень качества и проводить повторный аудит после существенных изменений сайта."],
                "definition_of_done": ["Повторный аудит не выявил новых критичных разрывов."],
                "verification": ["Запустить аудит после публикации крупных изменений и сравнить результат с текущим пакетом."],
                "expected_effect": "Позволяет удерживать достигнутый уровень качества и быстрее замечать регрессии.",
            }
        )
    return {
        "schema_version": TECHNICAL_SCHEMA_VERSION,
        "audit_id": review_brief["audit_id"],
        "package_status": review_brief["package_status"],
        "site": report_input["site"],
        "tasks": tasks,
        "checklist": [
            "Все P0- и P1-задачи внедрены на целевых URL и проверены в браузере.",
            "Повторный аудит подтвердил снижение приоритетных gaps.",
            "На ключевых шаблонах не появилось технических или контентных регрессий после внедрения.",
        ],
    }


def render_commercial_offer_md(doc: dict) -> str:
    lines = [
        f"# Коммерческое предложение для {doc['site']['primary_domain']}",
        "",
        "## 1. Цель сотрудничества",
        doc["sections"]["goal"],
        "",
        "## 2. Пакеты услуг",
    ]
    for package in doc["packages"]:
        lines.append(f"### {package['name']}")
        lines.append(f"- Стоимость: {package['price']}")
        lines.append("- Что входит:")
        for item in package["deliverables"]:
            lines.append(f"  - {item}")
        lines.append("- Ценность для клиента:")
        for item in package["value"]:
            lines.append(f"  - {item}")
        lines.append("")
    lines.extend(
        [
            "## 3. Рекомендуемый стартовый пакет",
            f"- Рекомендуем начать с: **{doc['recommended_package']}**",
            "- Причина: этот пакет лучше всего закрывает критичные разрывы текущего аудита и создает фундамент для следующих этапов.",
            "",
            "## 4. Этапность работ",
        ]
    )
    for item in doc["sections"]["phases"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 5. Что нужно от клиента"])
    for item in doc["sections"]["client_requirements"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 6. Важные оговорки"])
    for item in doc["sections"]["disclaimer"]:
        lines.append(f"- {item}")
    return "\n".join(lines).strip() + "\n"


def render_technical_action_plan_md(doc: dict) -> str:
    lines = [
        f"# Подробный технический план работ по сайту {doc['site']['primary_domain']}",
        "",
        "## 1. Цель документа",
        "Дать команде внедрения понятный список задач: что именно менять, где менять, как принять работу и как проверить эффект.",
        "",
        "## 2. Детальные задачи",
        "",
    ]
    for task in doc["tasks"]:
        lines.append(f"### {task['task_id']}: {task['title']} ({task['priority']})")
        lines.append(f"**Проблема:** {task['problem_statement']}")
        lines.append("")
        lines.append("**Что видим сейчас:**")
        for item in task["current_observations"]:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("**Где менять:**")
        for item in task["where_to_change"]:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("**URL для приоритета внедрения:**")
        for url in task["target_pages"] or ["Ключевые коммерческие и сервисные страницы"]:
            lines.append(f"- `{url}`" if str(url).startswith("http") else f"- {url}")
        lines.append("")
        lines.append("**Шаги реализации:**")
        for idx, step in enumerate(task["implementation_steps"], start=1):
            lines.append(f"{idx}. {step}")
        lines.append("")
        lines.append("**Критерии готовности:**")
        for item in task["definition_of_done"]:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("**Как проверять:**")
        for item in task["verification"]:
            lines.append(f"- {item}")
        lines.append("")
        lines.append(f"**Ожидаемый эффект:** {task['expected_effect']}")
        lines.append("")
    lines.extend(["## 3. Контрольный чек-лист после внедрения", ""])
    for item in doc["checklist"]:
        lines.append(f"- [ ] {item}")
    return "\n".join(lines).strip() + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 scripts/generate_commercial_documents.py <audit_package_dir>", file=sys.stderr)
        return 1
    package_dir = Path(argv[1])
    issues = ensure_approved(package_dir)
    if issues:
        print("commercial document generation blocked", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1
    ensure_client_report(package_dir)
    exports_dir = package_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    commercial_offer = build_commercial_offer(package_dir)
    technical_plan = build_technical_action_plan(package_dir)
    (exports_dir / "commercial_offer.json").write_text(json.dumps(commercial_offer, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    (exports_dir / "commercial_offer.md").write_text(render_commercial_offer_md(commercial_offer), encoding="utf-8")
    (exports_dir / "technical_action_plan.json").write_text(json.dumps(technical_plan, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    (exports_dir / "technical_action_plan.md").write_text(render_technical_action_plan_md(technical_plan), encoding="utf-8")
    sync_manifest_documents(package_dir)
    print("commercial documents generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
