#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from python.common.validators import validate_contracts, validate_evidence, validate_prompts
from scripts.delivery_i18n import translate_gap, translate_phrase


SCHEMA_VERSION = "1.0.0"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sync_manifest_client_report_input(package_dir: Path) -> None:
    manifest_path = package_dir / "manifest.json"
    manifest = load_json(manifest_path)
    manifest.setdefault("schema_versions", {})["client_report_input"] = SCHEMA_VERSION
    files = manifest.setdefault("files", [])
    entry = {
        "path": "exports/client_report_input.json",
        "category": "export",
        "required": False,
        "schema": "client_report_input",
        "checksum": sha256_file(package_dir / "exports" / "client_report_input.json"),
    }
    for index, item in enumerate(files):
        if item.get("path") == "exports/client_report_input.json":
            files[index] = entry
            break
    else:
        files.append(entry)
    files.sort(key=lambda item: item.get("path", ""))
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def ensure_approved(package_dir: Path) -> list[str]:
    issues = validate_contracts(
        package_dir,
        ignored_paths=(
            "exports/review_brief.json",
            "exports/summary.json",
            "exports/backlog.json",
            "exports/client_report_input.json",
            "exports/client_report.json",
            "exports/scoring_parity_snapshot.json",
            "exports/expert_report.json",
            "exports/technical_client_report.json",
            "exports/commercial_offer.json",
            "exports/technical_action_plan.json",
        ),
    ) + validate_evidence(package_dir) + validate_prompts(package_dir)
    manifest = load_json(package_dir / "manifest.json")
    if manifest.get("stage_status", {}).get("validate") != "completed":
        issues.append("package validate stage is not completed")
    normalized: list[str] = []
    for issue in issues:
        if isinstance(issue, str):
            normalized.append(issue)
        else:
            normalized.append(f"{issue.path}: {issue.message}")
    return normalized


def first_page_url(entities: dict) -> str:
    for entity in entities.get("entities", []):
        if entity.get("type") == "page" and entity.get("label"):
            return str(entity["label"])
    return ""


def primary_domain(url: str) -> str:
    parsed = urlparse(url)
    return (parsed.netloc or parsed.path).split(":")[0].strip("/")


def average_dimensions(score_items: list[dict]) -> dict[str, float]:
    labels = ("SEO", "GEO", "AEO", "AIO", "LEO")
    if not score_items:
        return {label: 0.0 for label in labels}
    result: dict[str, float] = {}
    for label in labels:
        values = [float(item.get("scores", {}).get(label, 0.0)) for item in score_items]
        result[label] = round(sum(values) / len(values), 4) if values else 0.0
    return result


def load_legacy_indices(package_dir: Path) -> list[dict]:
    path = package_dir / "analysis" / "legacy_index_scores.json"
    if not path.exists():
        return []
    payload = load_json(path)
    labels = {
        "ai_readiness": "AI Readiness",
        "generative_visibility": "Generative Visibility",
        "answer_fitness": "Answer Fitness",
    }
    result: list[dict] = []
    for key in ("ai_readiness", "generative_visibility", "answer_fitness"):
        item = payload.get("indices", {}).get(key)
        if not item:
            continue
        coverage = item.get("coverage", {})
        result.append(
            {
                "key": key,
                "label": labels[key],
                "score": float(item.get("score", 0.0)),
                "description": str(item.get("description", "")),
                "measured_factor_count": int(coverage.get("measured_factor_count", 0)),
                "total_factor_count": int(coverage.get("total_factor_count", 0)),
                "levels_covered": list(coverage.get("levels_covered", [])),
            }
        )
    return result


def infer_priority_area_label(page_type: str) -> str:
    labels = {
        "homepage": "Главная страница и первое доверие",
        "service": "Ключевые сервисные страницы",
        "category": "Коммерческие категории",
        "contacts": "Контакты и каналы связи",
        "delivery": "Доставка и условия получения",
        "return_policy": "Возвраты и гарантийные условия",
        "wholesale": "Оптовое предложение",
        "product": "Карточки продуктов",
        "article": "Информационный контент",
    }
    return labels.get(page_type, "Ключевые страницы сайта")


def infer_impact_text(page_type: str) -> str:
    if page_type in {"homepage", "service", "contacts"}:
        return "Влияет на доверие, понимание предложения и вероятность обращения."
    if page_type in {"delivery", "return_policy", "wholesale"}:
        return "Влияет на коммерческую ясность, снижение сомнений и качество лидов."
    if page_type in {"category", "product"}:
        return "Влияет на видимость коммерческих страниц и конвертацию спроса."
    return "Влияет на общую читаемость сайта для поисковых и AI-систем."


def site_profile_label(site_profile: str) -> str:
    labels = {
        "service": "сервисный сайт",
        "ecommerce": "коммерческий сайт",
        "mixed": "смешанный сайт",
    }
    return labels.get(site_profile, "сайт")


def health_band_label(lead_value_index: float) -> str:
    if lead_value_index >= 70:
        return "сильный уровень"
    if lead_value_index >= 40:
        return "рабочий уровень"
    if lead_value_index >= 15:
        return "зона улучшений"
    return "слабый уровень"


def format_decimal(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.1f}".rstrip("0").rstrip(".")


def russian_plural(count: int, one: str, few: str, many: str) -> str:
    value = abs(count) % 100
    if 11 <= value <= 14:
        return many
    tail = value % 10
    if tail == 1:
        return one
    if 2 <= tail <= 4:
        return few
    return many


def russian_count(count: int, one: str, few: str, many: str) -> str:
    return f"{count} {russian_plural(count, one, few, many)}"


def translate_action_summary(text: str) -> str:
    translated = translate_phrase(text)
    if translated != text:
        return translated
    prefix = "Add or verify blocks: "
    if text.startswith(prefix):
        raw_items = [item.strip() for item in text[len(prefix):].split(",") if item.strip()]
        return "Добавить или проверить блоки: " + ", ".join(translate_gap(item) for item in raw_items)
    return text


def translate_constraint(text: str) -> str:
    translated = translate_phrase(text)
    if translated != text:
        return translated
    return text


def build_report_input(package_dir: Path) -> dict:
    review_brief = load_json(package_dir / "exports/review_brief.json")
    entities = load_json(package_dir / "analysis/entities.json")
    scores = load_json(package_dir / "analysis/ai_readiness_scores.json")
    legacy_scores = load_legacy_indices(package_dir)

    primary_url = first_page_url(entities)
    site_profile = review_brief.get("executive_summary", {}).get("site_profile", "mixed")
    lead_value_index = float(scores.get("lead_value_index", 0.0))
    page_count = int(review_brief.get("summary", {}).get("page_count", 0))
    p0_targets = int(review_brief.get("summary", {}).get("p0_coverage_targets", 0))
    high_contradictions = int(review_brief.get("summary", {}).get("high_contradiction_count", 0))
    top_gaps = list(review_brief.get("top_gaps", []))
    translated_top_gaps = [translate_gap(str(item)) for item in top_gaps]
    crawl_quality = review_brief.get("crawl_quality", {})
    focus_areas = review_brief.get("focus_areas", [])
    priority_pages = review_brief.get("priority_pages", [])
    priority_areas = [
        {
            "label": infer_priority_area_label(str(area.get("page_type", "generic"))),
            "why_it_matters": infer_impact_text(str(area.get("page_type", "generic"))),
            "top_missing": list(area.get("top_missing", [])),
        }
        for area in focus_areas
    ]

    action_plan = [
        {
            **item,
            "summary": translate_action_summary(str(item.get("summary", ""))),
            "expected_impact": translate_action_summary(str(item.get("expected_impact", ""))),
        }
        for item in review_brief.get("action_plan", [])
    ]
    constraints = [translate_constraint(str(item)) for item in crawl_quality.get("warnings", [])]
    constraints.append("Отчетный входной пакет собран только из утвержденных артефактов пакета без генерации новых фактов.")
    overview = (
        f"Аудит показал, что {site_profile_label(site_profile)} сейчас находится в состоянии "
        f"«{health_band_label(lead_value_index)}» по клиентской и цифровой логике готовности сайта. "
        f"В анализ вошли {russian_count(page_count, 'страница', 'страницы', 'страниц')}, "
        f"индекс потенциала заявок составляет {format_decimal(lead_value_index)} из 100 — это оценка того, "
        f"насколько текущая структура и содержание сайта помогают превращать интерес в реальные обращения."
    )
    primary_risk = (
        f"Главный риск сейчас — {russian_count(p0_targets, 'высокоприоритетная зона покрытия', 'высокоприоритетные зоны покрытия', 'высокоприоритетных зон покрытия')}, "
        f"в первую очередь в блоках {', '.join(translated_top_gaps[:2]) if translated_top_gaps else 'контентной полноты'}."
    )
    primary_opportunity = (
        f"Главная возможность роста — усилить ключевые бизнес-страницы без потери текущего охвата обхода сайта "
        f"({russian_count(int(crawl_quality.get('html_count', 0)), 'HTML-страница', 'HTML-страницы', 'HTML-страниц')} в анализе)."
    )
    if high_contradictions > 0:
        next_step = (
            f"Следующий шаг: сначала закрыть противоречия и P0-гепы, затем собрать план правок по "
            f"блоку «{translated_top_gaps[0]}»." if translated_top_gaps else
            "Следующий шаг: сначала закрыть противоречия и P0-гепы, затем собрать план правок по ключевым блокам."
        )
    else:
        next_step = (
            f"Следующий шаг: собрать план внедрения, начиная с "
            f"блока «{translated_top_gaps[0]}»." if translated_top_gaps else
            "Следующий шаг: собрать план внедрения, начиная с ключевых блоков доверия и структуры."
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "audit_id": review_brief["audit_id"],
        "package_status": review_brief["package_status"],
        "methodology": {
            "score_engine": "current_deterministic_coverage_scoring_v1",
            "legacy_reference": "legacy_scoring_weights_v0_2",
            "report_parity": "partial",
            "score_parity": "not_aligned",
        },
        "site": {
            "primary_domain": primary_domain(primary_url),
            "primary_url": primary_url,
            "site_profile": site_profile,
        },
        "summary": {
            "overview": overview,
            "primary_risk": primary_risk,
            "primary_opportunity": primary_opportunity,
            "next_step": next_step,
            "page_count": page_count,
            "p0_coverage_targets": p0_targets,
            "high_contradiction_count": high_contradictions,
        },
        "indices": {
            "lead_value_index": lead_value_index,
            "dimensions": average_dimensions(priority_pages or scores.get("page_scores", [])),
            "legacy_scores": legacy_scores,
        },
        "strengths": list(review_brief.get("current_strengths", [])),
        "priority_areas": priority_areas,
        "action_plan": action_plan,
        "constraints": constraints,
        "evidence_sources": list(review_brief.get("evidence_sources", [])),
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 scripts/build_client_report_input.py <audit_package_dir>", file=sys.stderr)
        return 1

    package_dir = Path(argv[1])
    issues = ensure_approved(package_dir)
    if issues:
        print("client report input generation blocked", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    exports_dir = package_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    payload = build_report_input(package_dir)
    (exports_dir / "client_report_input.json").write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    sync_manifest_client_report_input(package_dir)
    print("client report input generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
