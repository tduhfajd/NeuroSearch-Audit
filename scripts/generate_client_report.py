#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_client_report_input import (
    SCHEMA_VERSION as INPUT_SCHEMA_VERSION,
    build_report_input,
    ensure_approved,
    load_json,
    sync_manifest_client_report_input,
)
from scripts.delivery_i18n import translate_gap


SCHEMA_VERSION = "1.0.0"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sync_manifest_client_report(package_dir: Path) -> None:
    manifest_path = package_dir / "manifest.json"
    manifest = load_json(manifest_path)
    schema_versions = manifest.setdefault("schema_versions", {})
    schema_versions["client_report_input"] = INPUT_SCHEMA_VERSION
    schema_versions["client_report"] = SCHEMA_VERSION
    files = manifest.setdefault("files", [])
    desired = {
        "exports/client_report_input.json": {
            "path": "exports/client_report_input.json",
            "category": "export",
            "required": False,
            "schema": "client_report_input",
            "checksum": sha256_file(package_dir / "exports" / "client_report_input.json"),
        },
        "exports/client_report.json": {
            "path": "exports/client_report.json",
            "category": "export",
            "required": False,
            "schema": "client_report",
            "checksum": sha256_file(package_dir / "exports" / "client_report.json"),
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


def score_band(value: float) -> str:
    if value >= 0.8:
        return "сильный уровень"
    if value >= 0.6:
        return "рабочий уровень"
    if value >= 0.4:
        return "зона улучшений"
    return "критическая зона"


def legacy_index_description(label: str) -> str:
    descriptions = {
        "AI Readiness": "Интегральная оценка готовности сайта к стабильной интерпретации, доверию и использованию в AI-сценариях.",
        "Generative Visibility": "Оценка того, насколько сайт заметен и пригоден для генеративной выдачи и AI-рекомендаций.",
        "Answer Fitness": "Оценка того, насколько сайт умеет быстро и однозначно отвечать на целевые вопросы пользователя.",
    }
    return descriptions[label]


def index_reading_guide() -> list[str]:
    return [
        "Индексы в этом отчёте рассчитаны по legacy-style весам, но только на том наборе факторов, который новая система реально умеет измерять из утвержденного audit_package.",
        "Значение ниже 40 означает критическую зону, 40–59 — зону улучшений, 60–79 — рабочий уровень, 80+ — сильный уровень.",
        "Смотрите не только на само число, но и на покрытие факторов: если индекс измерен по неполному набору факторов, его нужно читать осторожно.",
    ]


def build_how_to_use_section() -> list[dict[str, str]]:
    return [
        {
            "audience": "Руководитель",
            "guidance": "Смотрите на краткий вывод, интегральные индексы и план действий. Это карта ближайших решений по сайту, а не прогноз трафика или выручки.",
        },
        {
            "audience": "Маркетинг",
            "guidance": "Используйте приоритетные зоны улучшений как основу для контентного и структурного плана: что усилить на ключевых страницах и почему это влияет на видимость и доверие.",
        },
        {
            "audience": "Техническая команда",
            "guidance": "Используйте блок ограничений и план действий как вход в технический backlog: шаблоны страниц, разметка, структура, протокол, canonical и другие системные правки.",
        },
    ]


def build_priority_area_narratives(priority_areas: list[dict]) -> list[dict]:
    narratives: list[dict] = []
    for item in priority_areas:
        missing = [translate_gap(str(value)) for value in item.get("top_missing", [])]
        if missing:
            problem = f"Сейчас в этой зоне не хватает следующих элементов: {', '.join(missing)}."
        else:
            problem = "Сейчас в этой зоне нет достаточных сигналов для уверенного усиления страницы."
        narratives.append(
            {
                "label": item["label"],
                "why_it_matters": item["why_it_matters"],
                "current_state": problem,
            }
        )
    return narratives


def methodology_note(methodology: dict) -> str:
    legacy_reference = methodology.get("legacy_reference", "legacy_scoring_weights_v0_2")
    score_parity = methodology.get("score_parity", "not_aligned")
    if score_parity == "aligned":
        return (
            "Методологическая оговорка: индексы в этом отчёте рассчитаны по утвержденной весовой модели "
            f"`{legacy_reference}` и опираются только на данные утверждённого audit_package."
        )
    return (
        "Методологическая оговорка: индексы в этом отчёте рассчитаны по legacy-style весовой модели "
        f"`{legacy_reference}`, но только на измеряемом подмножестве факторов, которое новая система "
        "сейчас может объективно восстановить из утверждённого audit_package. Это не внешний стандарт "
        "и не обещание полного совпадения со старым MVP, а прозрачная рабочая оценка на текущем наборе данных."
    )


def build_client_report(report_input: dict) -> dict:
    methodology = report_input.get(
        "methodology",
        {
            "score_engine": "current_deterministic_coverage_scoring_v1",
            "legacy_reference": "legacy_scoring_weights_v0_2",
            "report_parity": "partial",
            "score_parity": "not_aligned",
        },
    )
    summary = report_input["summary"]
    indices = report_input["indices"]
    legacy_scores = indices.get("legacy_scores", [])
    executive_summary = [
        summary["overview"],
        summary["primary_risk"],
        summary["primary_opportunity"],
        summary["next_step"],
    ]
    what_was_evaluated = [
        {
            "label": item["label"],
            "description": legacy_index_description(item["label"]),
        }
        for item in legacy_scores
    ]
    rendered_indices = [
        {
            "label": item["label"],
            "value": round(float(item["score"]) * 100, 1),
            "interpretation": (
                f"{score_band(float(item['score']))}; "
                f"измерено факторов: {item['measured_factor_count']} из {item['total_factor_count']}."
            ),
        }
        for item in legacy_scores
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "audit_id": report_input["audit_id"],
        "package_status": report_input["package_status"],
        "methodology": methodology,
        "title": f"Аудит сайта {report_input['site']['primary_domain']}",
        "site": report_input["site"],
        "sections": {
            "executive_summary": executive_summary,
            "what_was_evaluated": what_was_evaluated,
            "index_reading_guide": index_reading_guide(),
            "indices": rendered_indices,
            "strengths": report_input["strengths"],
            "priority_areas": report_input["priority_areas"],
            "priority_area_narratives": build_priority_area_narratives(report_input["priority_areas"]),
            "action_plan": report_input["action_plan"],
            "constraints": report_input["constraints"],
            "how_to_use": build_how_to_use_section(),
        },
    }


def render_markdown(report: dict) -> str:
    lines = [
        "---",
        f'title: "{report["title"]}"',
        'date: ""',
        "---",
        "",
        f"> {methodology_note(report['methodology'])}",
        "",
        "# Краткий вывод",
        "",
    ]
    for item in report["sections"]["executive_summary"]:
        if item:
            lines.append(item)
            lines.append("")

    lines.extend(
        [
            "# Что оценивалось",
            "",
        ]
    )
    for item in report["sections"]["what_was_evaluated"]:
        lines.append(f'- **{item["label"]}**: {item["description"]}')
    lines.append("")

    lines.extend(["# Как читать индексы", ""])
    for item in report["sections"]["index_reading_guide"]:
        lines.append(f"- {item}")
    lines.append("")

    lines.extend(
        [
            "# Сводные индексы состояния",
            "",
            "| Индекс | Значение | Интерпретация |",
            "|---|---:|---|",
        ]
    )
    for item in report["sections"]["indices"]:
        lines.append(f'| {item["label"]} | {item["value"]} / 100 | {item["interpretation"]} |')
    lines.append("")

    if report["sections"]["strengths"]:
        lines.extend(["# Сильные стороны", ""])
        for item in report["sections"]["strengths"]:
            lines.append(f"- {item}")
        lines.append("")

    lines.extend(["# Ключевые зоны улучшений", ""])
    for area, narrative in zip(report["sections"]["priority_areas"], report["sections"]["priority_area_narratives"]):
        lines.append(f'## {area["label"]}')
        lines.append("")
        lines.append(f"Почему это важно: {narrative['why_it_matters']}")
        lines.append("")
        lines.append(f"Что видно по текущему аудиту: {narrative['current_state']}")
        lines.append("")
        if area["top_missing"]:
            lines.append("Что требует усиления:")
            for missing in area["top_missing"]:
                lines.append(f"- {translate_gap(str(missing))}")
            lines.append("")

    lines.extend(["# План действий", ""])
    for item in report["sections"]["action_plan"]:
        lines.append(f'## {item["priority"]}')
        lines.append("")
        lines.append(item["summary"])
        lines.append("")
        lines.append(f'Ожидаемый эффект: {item["expected_impact"]}')
        lines.append("")

    if report["sections"]["constraints"]:
        lines.extend(["# Ограничения и допущения", ""])
        for item in report["sections"]["constraints"]:
            lines.append(f"- {item}")
        lines.append("")

    lines.extend(["# Как использовать этот отчёт", ""])
    for item in report["sections"]["how_to_use"]:
        lines.append(f"## Для роли: {item['audience']}")
        lines.append("")
        lines.append(item["guidance"])
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 scripts/generate_client_report.py <audit_package_dir>", file=sys.stderr)
        return 1

    package_dir = Path(argv[1])
    issues = ensure_approved(package_dir)
    if issues:
        print("client report generation blocked", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    exports_dir = package_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    input_path = exports_dir / "client_report_input.json"
    if not input_path.exists():
        payload = build_report_input(package_dir)
        input_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        sync_manifest_client_report_input(package_dir)
    report_input = load_json(input_path)
    if "methodology" not in report_input:
        payload = build_report_input(package_dir)
        input_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        sync_manifest_client_report_input(package_dir)
        report_input = payload
    report = build_client_report(report_input)
    (exports_dir / "client_report.json").write_text(
        json.dumps(report, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (exports_dir / "client_report.md").write_text(render_markdown(report), encoding="utf-8")
    sync_manifest_client_report(package_dir)
    print("client report generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
