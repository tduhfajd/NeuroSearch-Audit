#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from python.common.validators import validate_contracts, validate_evidence, validate_prompts
from scripts.delivery_i18n import (
    translate_gap,
    translate_health_band,
    translate_page_type,
    translate_phrase,
    translate_site_profile,
)


SCHEMA_VERSION = "1.0.0"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sync_manifest_review_brief(package_dir: Path) -> None:
    manifest_path = package_dir / "manifest.json"
    manifest = load_json(manifest_path)
    manifest.setdefault("schema_versions", {})["review_brief"] = SCHEMA_VERSION
    files = manifest.setdefault("files", [])
    review_entry = {
        "path": "exports/review_brief.json",
        "category": "export",
        "required": False,
        "schema": "review_brief",
        "checksum": sha256_file(package_dir / "exports" / "review_brief.json"),
    }
    for index, entry in enumerate(files):
        if entry.get("path") == "exports/review_brief.json":
            files[index] = review_entry
            break
    else:
        files.append(review_entry)
    files.sort(key=lambda item: item.get("path", ""))
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def list_or_empty(value: object) -> list:
    if isinstance(value, list):
        return value
    return []


def infer_site_profile(entities: dict) -> str:
    counts: dict[str, int] = {}
    for entity in entities.get("entities", []):
        if entity.get("type") != "page":
            continue
        page_type = entity.get("attributes", {}).get("page_type", "generic")
        counts[page_type] = counts.get(page_type, 0) + 1
    commerce_count = sum(counts.get(key, 0) for key in ("product", "category", "delivery", "return_policy", "wholesale"))
    service_count = sum(counts.get(key, 0) for key in ("service", "homepage", "contacts", "about", "pricing", "case_study", "portfolio", "careers"))
    if commerce_count >= 4 and commerce_count >= service_count:
        return "ecommerce"
    if service_count > 0 and counts.get("product", 0) == 0 and counts.get("category", 0) == 0:
        return "service"
    return "mixed"


def health_band(lead_value_index: float) -> str:
    if lead_value_index >= 70:
        return "strong"
    if lead_value_index >= 40:
        return "moderate"
    if lead_value_index >= 15:
        return "limited"
    return "weak"


def format_number(value: float) -> str:
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


def ensure_approved(package_dir: Path) -> list[str]:
    issues = validate_contracts(
        package_dir,
        ignored_paths=(
            "exports/review_brief.json",
            "exports/summary.json",
            "exports/backlog.json",
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


def index_pages(entities: dict, coverage: dict, scores: dict) -> list[dict]:
    coverage_by_target = {item["target"]: item for item in coverage.get("items", [])}
    scores_by_url = {item["url"]: item for item in scores.get("page_scores", [])}
    pages: list[dict] = []
    page_type_weight = {
        "homepage": 100,
        "service": 95,
        "pricing": 92,
        "case_study": 91,
        "portfolio": 90,
        "about": 84,
        "careers": 35,
        "category": 90,
        "contacts": 85,
        "delivery": 84,
        "return_policy": 83,
        "wholesale": 82,
        "product": 70,
        "article": 60,
        "generic": 20,
    }
    priority_weight = {"P0": 100, "P1": 60, "P2": 20}
    page_type_caps = {
        "homepage": 1,
        "service": 3,
        "pricing": 2,
        "case_study": 2,
        "portfolio": 2,
        "about": 1,
        "careers": 1,
        "category": 3,
        "contacts": 1,
        "delivery": 2,
        "return_policy": 2,
        "wholesale": 1,
        "product": 4,
        "article": 2,
        "generic": 1,
    }
    for entity in sorted(entities.get("entities", []), key=lambda item: item["entity_id"]):
        if entity.get("type") != "page":
            continue
        url = entity.get("label", "")
        coverage_item = coverage_by_target.get(entity["entity_id"], {})
        score_item = scores_by_url.get(url, {})
        page_type = entity.get("attributes", {}).get("page_type", "unknown")
        missing = sorted(coverage_item.get("missing", []))
        if not missing and page_type == "generic":
            continue
        pages.append(
            {
                "entity_id": entity["entity_id"],
                "url": url,
                "page_type": page_type,
                "coverage_score": coverage_item.get("coverage_score", 0),
                "missing": missing,
                "scores": score_item.get("scores", {}),
                "_review_rank": (
                    priority_weight.get(coverage_item.get("priority", "P2"), 0)
                    + page_type_weight.get(page_type, 10),
                    len(missing),
                    -float(coverage_item.get("coverage_score", 0)),
                ),
            }
        )
    ordered = sorted(
        pages,
        key=lambda item: (-item["_review_rank"][0], -item["_review_rank"][1], item["_review_rank"][2], item["url"]),
    )
    deduped: list[dict] = []
    seen_urls: set[str] = set()
    for item in ordered:
        normalized_url = item["url"].rstrip("/") or item["url"]
        if normalized_url in seen_urls:
            continue
        seen_urls.add(normalized_url)
        deduped.append(item)
    trimmed: list[dict] = []
    selected_by_type: dict[str, int] = {}
    for item in deduped:
        page_type = item["page_type"]
        cap = page_type_caps.get(page_type, 1)
        if selected_by_type.get(page_type, 0) >= cap:
            continue
        selected_by_type[page_type] = selected_by_type.get(page_type, 0) + 1
        trimmed.append(item)
        if len(trimmed) == 12:
            break
    for item in trimmed:
        item.pop("_review_rank", None)
    return trimmed


def rank_top_gaps(entities: dict, coverage: dict) -> list[str]:
    entity_lookup = {entity["entity_id"]: entity for entity in entities.get("entities", [])}
    page_type_weight = {
        "homepage": 6,
        "service": 6,
        "pricing": 6,
        "case_study": 5,
        "portfolio": 5,
        "about": 4,
        "careers": 1,
        "category": 5,
        "contacts": 5,
        "delivery": 5,
        "return_policy": 5,
        "wholesale": 5,
        "product": 3,
        "article": 2,
        "generic": 1,
    }
    priority_weight = {"P0": 6, "P1": 3, "P2": 1}
    scores: dict[str, int] = {}
    for item in coverage.get("items", []):
        entity = entity_lookup.get(item["target"], {})
        page_type = entity.get("attributes", {}).get("page_type", "generic")
        base_weight = page_type_weight.get(page_type, 1) + priority_weight.get(item.get("priority", "P2"), 1)
        for gap in item.get("missing", []):
            scores[gap] = scores.get(gap, 0) + base_weight
    ordered = sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))
    return [gap for gap, _ in ordered[:8]]


def unique_evidence_sources(entities: dict, contradictions: dict) -> list[str]:
    sources: set[str] = set()
    for entity in entities.get("entities", []):
        for source_url in entity.get("source_urls", []):
            sources.add(source_url)
    for item in contradictions.get("contradictions", []):
        for source_url in item.get("sources", []):
            sources.add(source_url)
    return sorted(sources)


def build_executive_summary(entities: dict, coverage: dict, scores: dict, crawl_quality: dict, top_gaps: list[str]) -> dict:
    site_profile = infer_site_profile(entities)
    lead_value_index = float(scores.get("lead_value_index", 0))
    band = health_band(lead_value_index)
    p0_targets = int(coverage.get("summary", {}).get("p0", 0))
    page_count = len([item for item in entities.get("entities", []) if item.get("type") == "page"])
    policy_pages = sum(
        1
        for entity in entities.get("entities", [])
        if entity.get("type") == "page" and entity.get("attributes", {}).get("page_type") in {"contacts", "delivery", "return_policy", "wholesale"}
    )
    localized_gaps = [translate_gap(item) for item in top_gaps]
    policy_scope = (
        f"в {russian_count(policy_pages, 'приоритетном разделе доверия и условий', 'приоритетных разделах доверия и условий', 'приоритетных разделах доверия и условий')}"
        if policy_pages > 0
        else "в основных разделах доверия и условий"
    )
    overview = (
        f"Аудит показал, что {translate_site_profile(site_profile)} сейчас находится в состоянии "
        f"«{translate_health_band(band)}». В анализ вошли {russian_count(page_count, 'страница', 'страницы', 'страниц')}, "
        f"индекс потенциала заявок составляет {format_number(lead_value_index)}."
    )
    primary_risk = (
        f"Главный риск сейчас — {russian_count(p0_targets, 'высокоприоритетная зона покрытия', 'высокоприоритетные зоны покрытия', 'высокоприоритетных зон покрытия')}, "
        f"в первую очередь в блоках {', '.join(localized_gaps[:2]) if localized_gaps else 'полноты ключевого контента'}."
    )
    primary_opportunity = (
        f"Главная возможность роста — усилить ключевые бизнес-страницы "
        f"{policy_scope} "
        f"без потери текущего охвата обхода сайта в {russian_count(int(crawl_quality.get('html_count', 0)), 'HTML-странице', 'HTML-страницах', 'HTML-страницах')}."
    )
    next_step = (
        f"Следующий шаг: перевести в работу {russian_count(min(5, max(1, p0_targets)), 'приоритетное действие', 'приоритетных действия', 'приоритетных действий')} "
        f"и начать план внедрения с блока «{localized_gaps[0]}»." if localized_gaps else
        "Следующий шаг: перевести в работу приоритетные действия и начать план внедрения с ключевых блоков доверия и структуры."
    )
    return {
        "site_profile": site_profile,
        "health_band": band,
        "overview": overview,
        "primary_risk": primary_risk,
        "primary_opportunity": primary_opportunity,
        "next_step": next_step,
    }


def build_action_plan(recommendations: dict) -> list[dict]:
    plan: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for item in sorted(recommendations.get("recommendations", []), key=lambda value: (value["priority"], value["recommendation_id"])):
        criteria = list_or_empty(item.get("acceptance_criteria"))
        summary = translate_phrase(criteria[0]) if criteria else translate_phrase(item.get("expected_impact", "improve audit quality"))
        key = (item.get("priority", "P2"), summary)
        if key in seen:
            continue
        seen.add(key)
        plan.append(
            {
                "priority": item.get("priority", "P2"),
                "summary": summary,
                "expected_impact": translate_phrase(item.get("expected_impact", "")),
                "related_findings_count": len(list_or_empty(item.get("related_findings"))),
            }
        )
        if len(plan) == 6:
            break
    return plan


def localize_acceptance_criterion(text: str) -> str:
    translated = translate_phrase(text)
    if translated != text:
        return translated
    prefix = "Add or verify blocks: "
    if text.startswith(prefix):
        items = [item.strip() for item in text[len(prefix):].split(",") if item.strip()]
        return "Добавить или проверить блоки: " + ", ".join(translate_gap(item) for item in items)
    return text


def build_current_strengths(entities: dict, coverage: dict) -> list[str]:
    coverage_by_target = {item["target"]: item for item in coverage.get("items", [])}
    strengths: list[str] = []
    priority_page_types = ("homepage", "contacts", "about", "pricing", "case_study", "portfolio", "delivery", "return_policy", "wholesale", "service", "category")
    for page_type in priority_page_types:
        matching = [
            entity for entity in entities.get("entities", [])
            if entity.get("type") == "page"
            and entity.get("attributes", {}).get("page_type") == page_type
            and coverage_by_target.get(entity["entity_id"], {}).get("coverage_score", 0) >= 0.95
        ]
        if not matching:
            continue
        strengths.append(f"Страницы типа «{translate_page_type(page_type)}» уже дают сильное базовое покрытие.")
        if len(strengths) == 5:
            break
    return strengths


def build_focus_areas(priority_pages: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for page in priority_pages:
        if not page.get("missing"):
            continue
        page_type = page["page_type"]
        bucket = grouped.setdefault(page_type, {"page_type": page_type, "page_count": 0, "missing_counts": {}})
        bucket["page_count"] += 1
        for block in page.get("missing", []):
            bucket["missing_counts"][block] = bucket["missing_counts"].get(block, 0) + 1

    areas: list[dict] = []
    for bucket in grouped.values():
        ordered_missing = sorted(bucket["missing_counts"].items(), key=lambda pair: (-pair[1], pair[0]))
        areas.append(
            {
                "page_type": bucket["page_type"],
                "page_count": bucket["page_count"],
                "top_missing": [name for name, _ in ordered_missing[:3]],
            }
        )
    areas.sort(key=lambda item: (-item["page_count"], item["page_type"]))
    return areas[:5]


def build_crawl_quality(package_dir: Path) -> dict:
    visited = load_json(package_dir / "crawl/visited_urls.json")
    fetch_log = load_json(package_dir / "crawl/fetch_log.json")
    raw_pages = list((package_dir / "pages/raw").glob("*.json"))

    fetched_entries = [item for item in fetch_log.get("entries", []) if item.get("status") == "fetched"]
    html_count = 0
    non_html_count = 0
    submitted_count = 0
    sitemap_count = 0
    discovered_count = 0
    for item in fetched_entries:
        source = str(item.get("source", ""))
        if source == "submitted":
            submitted_count += 1
        elif source == "sitemap":
            sitemap_count += 1
        elif source == "discovered":
            discovered_count += 1
        content_type = str(item.get("content_type", "")).lower()
        if "text/html" in content_type or "application/xhtml+xml" in content_type or content_type == "":
            html_count += 1
        else:
            non_html_count += 1

    warnings: list[str] = []
    visited_urls = list_or_empty(visited.get("visited_urls"))
    skipped_urls = list_or_empty(visited.get("skipped_urls"))
    filtered_urls = list_or_empty(visited.get("filtered_urls"))
    filtered_count = len(filtered_urls)
    protocol_schemes = {str(url).split("://", 1)[0] for url in visited_urls if "://" in str(url)}
    protocol_duplication = "http" in protocol_schemes and "https" in protocol_schemes
    if non_html_count > 0:
        warnings.append("crawl included non-html fetches; review fetch_log for low-value targets")
    if filtered_count > html_count and filtered_count > 0:
        warnings.append("crawl policy filtered more urls than were persisted as html pages")
    if sitemap_count == 0:
        warnings.append("crawl did not use sitemap-seeded urls; review robots.txt and sitemap availability")
    if protocol_duplication:
        warnings.append("crawl observed both http and https urls; normalize redirects, canonical tags, sitemap, and internal links to https")

    if sitemap_count > 0 and discovered_count > 0:
        discovery_mode = "mixed"
    elif sitemap_count > 0:
        discovery_mode = "sitemap-led"
    elif discovered_count > 0:
        discovery_mode = "homepage-led"
    else:
        discovery_mode = "submitted-only"

    return {
        "visited_url_count": len(visited_urls),
        "skipped_url_count": len(skipped_urls),
        "filtered_url_count": filtered_count,
        "fetch_failure_count": int(visited.get("failure_count", 0)),
        "fetched_count": len(fetched_entries),
        "html_count": html_count,
        "non_html_count": non_html_count,
        "raw_page_count": len(raw_pages),
        "submitted_count": submitted_count,
        "sitemap_count": sitemap_count,
        "discovered_count": discovered_count,
        "discovery_mode": discovery_mode,
        "protocol_duplication": protocol_duplication,
        "warnings": warnings,
    }


def build_review_brief(package_dir: Path) -> dict:
    manifest = load_json(package_dir / "manifest.json")
    entities = load_json(package_dir / "analysis/entities.json")
    coverage = load_json(package_dir / "analysis/coverage_report.json")
    contradictions = load_json(package_dir / "analysis/contradictions.json")
    scores = load_json(package_dir / "analysis/ai_readiness_scores.json")
    recommendations = load_json(package_dir / "analysis/recommendations.json")
    crawl_quality = build_crawl_quality(package_dir)
    top_gaps = rank_top_gaps(entities, coverage)
    priority_pages = index_pages(entities, coverage, scores)
    action_plan = build_action_plan(recommendations)
    current_strengths = build_current_strengths(entities, coverage)
    focus_areas = build_focus_areas(priority_pages)
    executive_summary = build_executive_summary(entities, coverage, scores, crawl_quality, top_gaps)

    high_contradictions = sorted(
        [
            {
                "contradiction_id": item["contradiction_id"],
                "type": item["type"],
                "severity": item["severity"],
                "sources": sorted(item.get("sources", [])),
                "risk": sorted(item.get("risk", [])),
            }
            for item in contradictions.get("contradictions", [])
            if item.get("severity") == "high"
        ],
        key=lambda item: item["contradiction_id"],
    )

    priority_recommendations = sorted(
        [
            {
                "recommendation_id": item["recommendation_id"],
                "priority": item["priority"],
                "expected_impact": item["expected_impact"],
                "acceptance_criteria": item.get("acceptance_criteria", []),
                "related_findings": sorted(item.get("related_findings", [])),
            }
            for item in recommendations.get("recommendations", [])
        ],
        key=lambda item: (item["priority"], item["recommendation_id"]),
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "audit_id": manifest["audit_id"],
        "package_status": "approved",
        "lead_value_index": scores.get("lead_value_index", 0),
        "summary": {
            "page_count": len([item for item in entities.get("entities", []) if item.get("type") == "page"]),
            "high_contradiction_count": len(high_contradictions),
            "p0_coverage_targets": coverage.get("summary", {}).get("p0", 0),
            "validate_status": manifest.get("stage_status", {}).get("validate", "pending"),
        },
        "executive_summary": executive_summary,
        "crawl_quality": crawl_quality,
        "top_gaps": top_gaps,
        "action_plan": action_plan,
        "current_strengths": current_strengths,
        "focus_areas": focus_areas,
        "priority_pages": priority_pages,
        "high_contradictions": high_contradictions,
        "priority_recommendations": priority_recommendations[:5],
        "evidence_sources": unique_evidence_sources(entities, contradictions),
    }


def render_markdown(brief: dict) -> str:
    lines: list[str] = []
    lines.append("# Краткий обзор аудита")
    lines.append("")
    lines.append(f"- Audit ID: `{brief['audit_id']}`")
    lines.append(f"- Статус пакета: `{brief['package_status']}`")
    lines.append(f"- Индекс потенциала заявок: `{brief['lead_value_index']}`")
    lines.append(f"- Страницы: `{brief['summary']['page_count']}`")
    lines.append(f"- Критичные противоречия: `{brief['summary']['high_contradiction_count']}`")
    lines.append(f"- P0-цели покрытия: `{brief['summary']['p0_coverage_targets']}`")
    lines.append(f"- Профиль сайта: `{translate_site_profile(brief['executive_summary']['site_profile'])}`")
    lines.append(f"- Состояние: `{translate_health_band(brief['executive_summary']['health_band'])}`")
    lines.append(f"- HTML-страницы в обходе: `{brief['crawl_quality']['html_count']}`")
    lines.append(f"- Отфильтрованные URL: `{brief['crawl_quality']['filtered_url_count']}`")
    lines.append(f"- Не-HTML ответы: `{brief['crawl_quality']['non_html_count']}`")
    lines.append(f"- Режим обнаружения страниц: `{translate_phrase(brief['crawl_quality']['discovery_mode'])}`")
    lines.append(
        f"- Источники обнаружения: submitted=`{brief['crawl_quality']['submitted_count']}`, sitemap=`{brief['crawl_quality']['sitemap_count']}`, discovered=`{brief['crawl_quality']['discovered_count']}`"
    )
    if brief["crawl_quality"]["warnings"]:
        lines.append("- Предупреждения по обходу:")
        for item in brief["crawl_quality"]["warnings"]:
            lines.append(f"  - {translate_phrase(item)}")
    lines.append("")
    lines.append("## Краткий вывод")
    lines.append("")
    lines.append(f"- {brief['executive_summary']['overview']}")
    lines.append(f"- {brief['executive_summary']['primary_risk']}")
    lines.append(f"- {brief['executive_summary']['primary_opportunity']}")
    lines.append(f"- {brief['executive_summary']['next_step']}")
    lines.append("")
    lines.append("## Главные разрывы")
    lines.append("")
    for item in brief["top_gaps"]:
        lines.append(f"- `{translate_gap(item)}`")
    lines.append("")
    if brief["current_strengths"]:
        lines.append("## Что уже работает")
        lines.append("")
        for item in brief["current_strengths"]:
            lines.append(f"- {item}")
        lines.append("")
    if brief["focus_areas"]:
        lines.append("## Ключевые зоны внимания")
        lines.append("")
        for item in brief["focus_areas"]:
            lines.append(
                f"- `{translate_page_type(item['page_type'])}`: {russian_count(item['page_count'], 'страница в зоне внимания', 'страницы в зоне внимания', 'страниц в зоне внимания')}; "
                f"повторяющиеся разрывы: {', '.join(translate_gap(gap) for gap in item['top_missing'])}"
            )
        lines.append("")
    lines.append("## План действий")
    lines.append("")
    for item in brief["action_plan"]:
        lines.append(f"- [{item['priority']}] {item['summary']}")
        lines.append(f"  - Ожидаемый эффект: {item['expected_impact']}")
        lines.append(f"  - Связанные проблемы: {item['related_findings_count']}")
    lines.append("")
    lines.append("## Приоритетные страницы")
    lines.append("")
    for page in brief["priority_pages"]:
        lines.append(f"### `{page['url']}`")
        lines.append(f"- Тип страницы: `{translate_page_type(page['page_type'])}`")
        lines.append(f"- Покрытие: `{page['coverage_score']}`")
        lines.append(f"- Не хватает: {', '.join(translate_gap(gap) for gap in page['missing']) if page['missing'] else 'нет'}")
        if page["scores"]:
            score_items = ", ".join(f"{name}={value}" for name, value in sorted(page["scores"].items()))
            lines.append(f"- Индексы: {score_items}")
        lines.append("")
    lines.append("## Критичные противоречия")
    lines.append("")
    if brief["high_contradictions"]:
        for item in brief["high_contradictions"]:
            lines.append(f"- `{item['contradiction_id']}`: `{item['type']}`; источники: {', '.join(item['sources'])}")
    else:
        lines.append("- нет")
    lines.append("")
    lines.append("## Приоритетные рекомендации")
    lines.append("")
    for item in brief["priority_recommendations"]:
        lines.append(f"- `{item['recommendation_id']}` [{item['priority']}] {translate_phrase(item['expected_impact'])}")
        for criterion in item["acceptance_criteria"]:
            lines.append(f"  - {localize_acceptance_criterion(criterion)}")
    lines.append("")
    lines.append("## Источники доказательств")
    lines.append("")
    for source in brief["evidence_sources"]:
        lines.append(f"- {source}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 scripts/generate_review_artifacts.py <audit_package_dir>", file=sys.stderr)
        return 1

    package_dir = Path(argv[1])
    issues = ensure_approved(package_dir)
    if issues:
        print("review artifact generation blocked", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    exports_dir = package_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)

    brief = build_review_brief(package_dir)
    (exports_dir / "review_brief.json").write_text(
        json.dumps(brief, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (exports_dir / "review_brief.md").write_text(render_markdown(brief) + "\n", encoding="utf-8")
    sync_manifest_review_brief(package_dir)

    print("review artifacts generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
