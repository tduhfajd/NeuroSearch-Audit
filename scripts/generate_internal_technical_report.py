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


SCHEMA_VERSION = "1.0.0"

CONTRADICTION_TITLES = {
    "contact_email_conflict": "Конфликт контактных email-адресов",
    "contact_phone_conflict": "Конфликт контактных телефонов",
    "price_conflict": "Конфликт ценовых значений",
    "geo_conflict": "Конфликт географии или зоны обслуживания",
    "terms_conflict": "Конфликт условий и политик",
    "timeline_conflict": "Конфликт сроков",
}

CONTRADICTION_ACTIONS = {
    "contact_email_conflict": [
        "Выбрать один канонический email для сайта или для каждого допустимого раздела.",
        "Привести header, footer, контакты, формы и шаблоны писем к одному адресу.",
        "Проверить, что email совпадает в виджетах, карточках контактов и служебных страницах.",
    ],
    "contact_phone_conflict": [
        "Выбрать один канонический телефон для сайта или для каждого допустимого раздела.",
        "Привести header, footer, контакты и конверсионные блоки к одному значению.",
        "Проверить, что телефон совпадает в шаблонах, микроразметке и виджетах связи.",
    ],
    "price_conflict": [
        "Определить единую модель цены: фиксированная цена, диапазон или цена от.",
        "Синхронизировать карточки товаров, категории, условия доставки и коммерческие блоки.",
        "Если варианты цены допустимы, явно подписать, к какому пакету или сценарию относится каждое значение.",
    ],
    "geo_conflict": [
        "Утвердить одну формулировку по географии продаж и доставки.",
        "Синхронизировать контактные страницы, карточки товаров и коммерческие разделы.",
        "Если есть разные регионы или сценарии доставки, описать их как отдельные правила, а не как конфликтующие утверждения.",
    ],
    "terms_conflict": [
        "Зафиксировать каноническую редакцию условий доставки, обмена, возврата и гарантии.",
        "Обновить все страницы, где эти условия упоминаются, до единой формулировки.",
        "Проверить, что юридически значимые условия не расходятся между страницами и шаблонами.",
    ],
    "timeline_conflict": [
        "Определить единую формулировку сроков изготовления, доставки и возврата.",
        "Разделить разные сроки по типам заказа, если это действительно разные сценарии.",
        "Обновить витрину, FAQ и информационные страницы так, чтобы сроки не противоречили друг другу.",
    ],
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sync_manifest(package_dir: Path) -> None:
    manifest_path = package_dir / "manifest.json"
    manifest = load_json(manifest_path)
    manifest.setdefault("schema_versions", {})["internal_technical_report"] = SCHEMA_VERSION
    files = manifest.setdefault("files", [])
    entry = {
        "path": "exports/internal_technical_report.md",
        "category": "export",
        "required": False,
        "schema": "",
        "checksum": sha256_file(package_dir / "exports" / "internal_technical_report.md"),
    }
    for index, item in enumerate(files):
        if item.get("path") == entry["path"]:
            files[index] = entry
            break
    else:
        files.append(entry)
    files.sort(key=lambda item: item.get("path", ""))
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def load_technical_pages(package_dir: Path) -> list[dict]:
    pages = []
    for path in sorted((package_dir / "pages" / "technical").glob("*.json")):
        pages.append(load_json(path))
    return pages


def summarize_page_signals(pages: list[dict]) -> dict:
    missing_h1 = []
    missing_meta = []
    missing_title = []
    missing_canonical = []
    non_https_canonical = []
    missing_hsts = []
    mixed_content = []

    for page in pages:
        url = str(page.get("url", "")).strip()
        headings = page.get("headings", {}) or {}
        meta = page.get("meta", {}) or {}
        transport = page.get("transport_signals", {}) or {}
        canonical_url = str(page.get("canonical_url") or "").strip()

        if not str(page.get("title") or "").strip():
            missing_title.append(url)
        if not headings.get("h1"):
            missing_h1.append(url)
        if not str(meta.get("description") or "").strip():
            missing_meta.append(url)
        if not canonical_url:
            missing_canonical.append(url)
        elif canonical_url.startswith("http://"):
            non_https_canonical.append(url)
        if not str(transport.get("strict_transport_security") or "").strip():
            missing_hsts.append(url)
        if transport.get("mixed_content_urls"):
            mixed_content.append(url)

    return {
        "page_count": len(pages),
        "missing_title": missing_title,
        "missing_h1": missing_h1,
        "missing_meta": missing_meta,
        "missing_canonical": missing_canonical,
        "non_https_canonical": non_https_canonical,
        "missing_hsts": missing_hsts,
        "mixed_content": mixed_content,
    }


def build_summary_items(signal_summary: dict) -> list[dict]:
    items = []

    def add_item(title: str, urls: list[str], fix: str, priority: str = "P1") -> None:
        if not urls:
            return
        items.append(
            {
                "title": title,
                "priority": priority,
                "count": len(urls),
                "urls": urls[:12],
                "fix": fix,
            }
        )

    add_item(
        "На страницах отсутствует заголовок H1",
        signal_summary["missing_h1"],
        "Добавить один осмысленный H1 на каждую страницу и убедиться, что он соответствует назначению страницы.",
    )
    add_item(
        "На страницах отсутствует meta description",
        signal_summary["missing_meta"],
        "Заполнить meta description для целевых страниц, чтобы описание было уникальным и соответствовало реальному контенту.",
    )
    add_item(
        "На страницах отсутствует title",
        signal_summary["missing_title"],
        "Добавить уникальный title на каждую страницу.",
        priority="P0",
    )
    add_item(
        "На страницах отсутствует canonical",
        signal_summary["missing_canonical"],
        "Прописать canonical для страниц, где он отсутствует.",
        priority="P0",
    )
    add_item(
        "Canonical указывает на http-версию",
        signal_summary["non_https_canonical"],
        "Перевести canonical на https-версию URL.",
        priority="P0",
    )
    add_item(
        "На страницах отсутствует Strict-Transport-Security",
        signal_summary["missing_hsts"],
        "Включить заголовок Strict-Transport-Security на HTTPS-ответах и проверить его на приоритетных URL.",
        priority="P0",
    )
    add_item(
        "На страницах найден mixed content",
        signal_summary["mixed_content"],
        "Убрать http-ресурсы со страниц, которые открываются по https.",
        priority="P0",
    )
    return items


def build_contradiction_items(review_brief: dict) -> list[dict]:
    items = []
    for contradiction in review_brief.get("high_contradictions", []):
        contradiction_type = str(contradiction.get("type") or "").strip()
        items.append(
            {
                "title": CONTRADICTION_TITLES.get(contradiction_type, contradiction_type or "Противоречие в данных"),
                "priority": "P0" if contradiction.get("severity") == "high" else "P1",
                "count": len(contradiction.get("sources", [])),
                "urls": list(contradiction.get("sources", []))[:12],
                "fixes": CONTRADICTION_ACTIONS.get(
                    contradiction_type,
                    ["Выбрать одну каноническую версию данных и синхронизировать ее на всех затронутых страницах."],
                ),
                "risk": list(contradiction.get("risk", [])),
            }
        )
    return items


def build_priority_tasks(review_brief: dict) -> list[dict]:
    tasks = []
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for item in review_brief.get("priority_recommendations", [])[:8]:
        steps = tuple(str(step) for step in item.get("acceptance_criteria", [])[:6])
        key = (str(item.get("priority") or "P1"), steps)
        if key in seen:
            continue
        seen.add(key)
        tasks.append(
            {
                "priority": str(item.get("priority") or "P1"),
                "expected_impact": str(item.get("expected_impact") or "").strip(),
                "steps": list(steps),
            }
        )
    return tasks


def build_report(package_dir: Path) -> dict:
    report_input = load_json(package_dir / "exports" / "client_report_input.json")
    review_brief = load_json(package_dir / "exports" / "review_brief.json")
    pages = load_technical_pages(package_dir)
    signal_summary = summarize_page_signals(pages)

    return {
        "audit_id": review_brief["audit_id"],
        "domain": report_input["site"]["primary_domain"],
        "page_count": signal_summary["page_count"],
        "technical_summary": build_summary_items(signal_summary),
        "contradictions": build_contradiction_items(review_brief),
        "priority_tasks": build_priority_tasks(review_brief),
        "warnings": list((review_brief.get("crawl_quality") or {}).get("warnings", [])),
        "limits": list(report_input.get("constraints", [])),
    }


def render_markdown(report: dict) -> str:
    lines = [
        f"# Внутренний технический отчет по сайту {report['domain']}",
        "",
        "Документ предназначен для технической команды. Это рабочий список найденных недостатков, затронутых URL и шагов исправления.",
        "",
        "## 1. Объем проверки",
        "",
        f"- Audit ID: `{report['audit_id']}`",
        f"- Количество технических страниц в пакете: {report['page_count']}",
        "",
        "## 2. Сводка технических проблем",
        "",
    ]

    if report["technical_summary"]:
        for item in report["technical_summary"]:
            lines.append(f"### {item['title']} ({item['priority']})")
            lines.append(f"- Количество затронутых URL: {item['count']}")
            lines.append(f"- Что исправить: {item['fix']}")
            lines.append("- Основные URL:")
            for url in item["urls"]:
                lines.append(f"  - `{url}`")
            lines.append("")
    else:
        lines.append("- По базовым техническим сигналам критичных массовых дефектов не найдено.")
        lines.append("")

    lines.extend(["## 3. Противоречия в данных сайта", ""])
    if report["contradictions"]:
        for item in report["contradictions"]:
            lines.append(f"### {item['title']} ({item['priority']})")
            if item["risk"]:
                lines.append(f"- Риски: {', '.join(item['risk'])}")
            lines.append(f"- Количество затронутых URL: {item['count']}")
            lines.append("- Что сделать:")
            for step in item["fixes"]:
                lines.append(f"  - {step}")
            lines.append("- Где проверять в первую очередь:")
            for url in item["urls"]:
                lines.append(f"  - `{url}`")
            lines.append("")
    else:
        lines.append("- Высокоприоритетные противоречия в данных не зафиксированы.")
        lines.append("")

    lines.extend(["## 4. Приоритетные технические задачи", ""])
    if report["priority_tasks"]:
        for index, task in enumerate(report["priority_tasks"], start=1):
            lines.append(f"### TASK-{index:02d} ({task['priority']})")
            if task["expected_impact"]:
                lines.append(f"- Ожидаемый эффект: {task['expected_impact']}")
            lines.append("- Шаги:")
            for step in task["steps"]:
                lines.append(f"  - {step}")
            lines.append("")
    else:
        lines.append("- Приоритетные задачи не сформированы.")
        lines.append("")

    lines.extend(
        [
            "## 5. Проверка после внедрения",
            "",
            "- Повторно запустить аудит сайта после внедрения.",
            "- Проверить, что P0-проблемы исчезли из `review_brief.json` и `recommendations.json`.",
            "- Проверить вручную ключевые URL в браузере и через DevTools/response headers.",
            "- Убедиться, что исправления не внесли новые противоречия в цены, контакты, сроки и условия.",
            "",
        ]
    )

    if report["warnings"]:
        lines.extend(["## 6. Предупреждения по данным обхода", ""])
        for warning in report["warnings"]:
            lines.append(f"- {warning}")
        lines.append("")

    if report["limits"]:
        lines.extend(["## 7. Ограничения", ""])
        for item in report["limits"]:
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 scripts/generate_internal_technical_report.py <audit_package_dir>", file=sys.stderr)
        return 1
    package_dir = Path(argv[1])
    issues = ensure_approved(package_dir)
    if issues:
        print("internal technical report generation blocked", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1
    exports_dir = package_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(package_dir)
    (exports_dir / "internal_technical_report.md").write_text(render_markdown(report), encoding="utf-8")
    sync_manifest(package_dir)
    print("internal technical report generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
