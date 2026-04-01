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
from scripts.delivery_i18n import translate_gap, translate_phrase, translate_site_profile


SCHEMA_VERSION = "1.0.0"

ISSUE_LIBRARY = {
    "secure_protocol": {
        "title": "Протокол и единая техническая версия сайта",
        "diagnosis": "Сайт одновременно работает в http и https вариантах, поэтому технический сигнал распадается на две версии.",
        "business_risk": "Это снижает доверие к сайту, усложняет канонизацию и делает индексацию менее устойчивой.",
        "what_to_change": [
            "Закрепить единственную https-версию сайта как основную.",
            "Настроить редиректы, canonical, sitemap и внутренние ссылки только на https.",
        ],
    },
    "strict_transport_security": {
        "title": "Транспортная безопасность HTTPS-контура",
        "diagnosis": "HTTPS используется не как полностью закрепленный режим, потому что сервер не отдает Strict-Transport-Security.",
        "business_risk": "Это ослабляет сигнал доверия и оставляет протокольный контур менее стабильным, чем может быть.",
        "what_to_change": [
            "Включить заголовок Strict-Transport-Security для https-ответов.",
            "Проверить, что после включения HSTS сайт стабильно работает только в безопасном режиме.",
        ],
    },
    "messengers": {
        "title": "Быстрые каналы связи и сценарий первого контакта",
        "diagnosis": "На приоритетных страницах не хватает явного быстрого канала связи через мессенджеры или аналогичный instant-contact слой.",
        "business_risk": "Часть клиентов не доходит до обращения, потому что путь к первому контакту слишком длинный или неочевидный.",
        "what_to_change": [
            "Добавить видимый быстрый канал связи на главной и ключевых сервисных страницах.",
            "Сделать CTA-переход к контакту коротким и повторяемым на приоритетных шаблонах.",
        ],
    },
    "proof": {
        "title": "Социальное доказательство и подтверждение компетенции",
        "diagnosis": "Сайт недостаточно подтверждает опыт компании кейсами, цифрами, клиентами, отзывами или результатами.",
        "business_risk": "Пользователь видит описание услуг, но не получает достаточного основания доверять исполнителю.",
        "what_to_change": [
            "Добавить кейсы, цифры результата, клиентов, отзывы и другие доказательства опыта.",
            "Расположить proof-блоки рядом с ключевыми коммерческими тезисами и CTA.",
        ],
    },
    "pricing": {
        "title": "Ценовая и коммерческая ясность",
        "diagnosis": "На странице не хватает понятных сигналов о стоимости, диапазонах цены или коммерческих условиях.",
        "business_risk": "Клиент не понимает порог входа и раньше уходит из сценария обращения.",
        "what_to_change": [
            "Добавить диапазоны стоимости, модель ценообразования или объяснение, от чего зависит цена.",
            "Вывести коммерческие условия ближе к CTA и сценарию обращения.",
        ],
    },
    "process_steps": {
        "title": "Понятный сценарий работы и этапы внедрения",
        "diagnosis": "Сайт не объясняет по шагам, как будет идти работа с клиентом и что происходит после обращения.",
        "business_risk": "Отсутствие понятного процесса увеличивает сомнения и снижает конверсию в заявку.",
        "what_to_change": [
            "Добавить блок «этапы работы» или «как проходит проект» на приоритетных страницах.",
            "Привязать этапы к результату, срокам и следующему действию клиента.",
        ],
    },
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sync_manifest(package_dir: Path) -> None:
    manifest_path = package_dir / "manifest.json"
    manifest = load_json(manifest_path)
    manifest.setdefault("schema_versions", {})["technical_client_report"] = SCHEMA_VERSION
    files = manifest.setdefault("files", [])
    entry = {
        "path": "exports/technical_client_report.json",
        "category": "export",
        "required": False,
        "schema": "technical_client_report",
        "checksum": sha256_file(package_dir / "exports" / "technical_client_report.json"),
    }
    for index, item in enumerate(files):
        if item.get("path") == entry["path"]:
            files[index] = entry
            break
    else:
        files.append(entry)
    files.sort(key=lambda item: item.get("path", ""))
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def build_target_urls(review_brief: dict) -> list[str]:
    urls: list[str] = []
    for item in review_brief.get("priority_pages", []):
        url = str(item.get("url") or "").strip()
        if url and url not in urls:
            urls.append(url)
    return urls[:6]


def recommendation_steps(review_brief: dict) -> list[str]:
    steps: list[str] = []
    for recommendation in review_brief.get("priority_recommendations", [])[:3]:
        for criterion in recommendation.get("acceptance_criteria", [])[:4]:
            translated = translate_phrase(str(criterion))
            if translated not in steps:
                steps.append(translated)
    return steps


def build_issue(gap: str, review_brief: dict, target_urls: list[str], plan_steps: list[str], index: int) -> dict:
    template = ISSUE_LIBRARY.get(
        gap,
        {
            "title": translate_gap(gap).capitalize(),
            "diagnosis": f"На приоритетных страницах не хватает блока «{translate_gap(gap)}».",
            "business_risk": "Из-за этого сайт хуже объясняет предложение и теряет часть целевого спроса.",
            "what_to_change": [f"Добавить и стандартизировать блок «{translate_gap(gap)}» на ключевых страницах."],
        },
    )
    checked = [
        "Структура приоритетных страниц и наличие нужных блоков.",
        "Технические и доверительные сигналы на главной и ключевых URL.",
        "Текущие рекомендации, сформированные из approved package.",
    ]
    fixes = list(template["what_to_change"])
    if gap in {"secure_protocol", "strict_transport_security"}:
        for step in plan_steps:
            if step not in fixes:
                fixes.append(step)
    return {
        "issue_id": f"ISSUE-{index:02d}",
        "title": template["title"],
        "priority": "P0" if gap in {"secure_protocol", "strict_transport_security"} else "P1",
        "diagnosis": template["diagnosis"],
        "business_risk": template["business_risk"],
        "what_was_checked": checked,
        "target_urls": target_urls,
        "what_to_change": fixes,
        "acceptance_criteria": fixes[:4],
        "verification": [
            "Проверить изменения на целевых страницах вручную в браузере.",
            "Повторно запустить аудит и убедиться, что соответствующий gap перестал быть приоритетным.",
        ],
    }


def build_report(package_dir: Path) -> dict:
    review_brief = load_json(package_dir / "exports" / "review_brief.json")
    report_input = load_json(package_dir / "exports" / "client_report_input.json")
    target_urls = build_target_urls(review_brief)
    plan_steps = recommendation_steps(review_brief)
    gaps = [str(item) for item in review_brief.get("top_gaps", [])[:4]]
    issues = [build_issue(gap, review_brief, target_urls, plan_steps, index) for index, gap in enumerate(gaps, start=1)]
    crawl_quality = review_brief.get("crawl_quality", {})
    overview = [
        f"В анализ вошли {review_brief.get('summary', {}).get('page_count', 0)} страниц сайта и технические сигналы, которые были подтверждены approved package.",
        f"Сайт по текущему ruleset относится к профилю «{translate_site_profile(report_input.get('site', {}).get('site_profile', 'service'))}», при этом главные разрывы сосредоточены вокруг блоков: {', '.join(translate_gap(gap) for gap in gaps) if gaps else 'ключевых бизнес-сигналов'}.",
    ]
    if crawl_quality.get("protocol_duplication"):
        overview.append("Отдельно зафиксирован протокольный риск: сайт отдает одновременно http и https URL.")
    return {
        "schema_version": SCHEMA_VERSION,
        "audit_id": review_brief["audit_id"],
        "package_status": review_brief["package_status"],
        "site": report_input["site"],
        "summary": {
            "what_was_analyzed": [
                "Страницы, попавшие в approved audit package после обхода и фильтрации.",
                "Технические сигналы: протокол, canonical, transport-security, контакты и trust-блоки.",
                "Покрытие приоритетных страниц бизнес-значимыми блоками и текущие рекомендации по исправлению.",
            ],
            "overall_readout": overview,
            "limits": list(report_input.get("constraints", [])),
        },
        "issues": issues,
        "next_steps": [
            "Сначала устранить P0-задачи по протоколу и безопасности, если они есть.",
            "Затем закрыть пробелы в доверии, контактах и сценарии обращения на главной и ключевых сервисных страницах.",
            "После внедрения повторно прогнать аудит и зафиксировать, какие gaps ушли из приоритетных.",
        ],
    }


def render_markdown(report: dict) -> str:
    lines = [
        f"# Технический отчёт для клиента по сайту {report['site']['primary_domain']}",
        "",
        "## 1. Что анализировалось",
        "",
    ]
    for item in report["summary"]["what_was_analyzed"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 2. Общая техническая картина", ""])
    for item in report["summary"]["overall_readout"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 3. Выявленные недостатки и что с ними делать", ""])
    for issue in report["issues"]:
        lines.append(f"### {issue['issue_id']}: {issue['title']} ({issue['priority']})")
        lines.append(f"**Что обнаружено:** {issue['diagnosis']}")
        lines.append("")
        lines.append(f"**Почему это важно:** {issue['business_risk']}")
        lines.append("")
        lines.append("**Что проверяли:**")
        for item in issue["what_was_checked"]:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("**Где проблема проявляется в первую очередь:**")
        for url in issue["target_urls"]:
            lines.append(f"- `{url}`")
        lines.append("")
        lines.append("**Что нужно сделать:**")
        for item in issue["what_to_change"]:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("**Как понять, что проблема закрыта:**")
        for item in issue["acceptance_criteria"]:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("**Как проверить:**")
        for item in issue["verification"]:
            lines.append(f"- {item}")
        lines.append("")
    lines.extend(["## 4. Следующие шаги", ""])
    for item in report["next_steps"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 5. Ограничения и допущения", ""])
    for item in report["summary"]["limits"]:
        lines.append(f"- {item}")
    return "\n".join(lines).strip() + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 scripts/generate_technical_client_report.py <audit_package_dir>", file=sys.stderr)
        return 1
    package_dir = Path(argv[1])
    issues = ensure_approved(
        package_dir,
    )
    if issues:
        print("technical client report generation blocked", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1
    exports_dir = package_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(package_dir)
    (exports_dir / "technical_client_report.json").write_text(
        json.dumps(report, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (exports_dir / "technical_client_report.md").write_text(render_markdown(report), encoding="utf-8")
    sync_manifest(package_dir)
    print("technical client report generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
