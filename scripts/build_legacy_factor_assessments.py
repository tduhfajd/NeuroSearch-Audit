#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_client_report_input import ensure_approved, load_json


SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class FactorSpec:
    factor_id: str
    name: str
    tier: str
    level: str
    measure_key: str


FACTOR_SPECS = (
    FactorSpec("F-TECH-002", "Корректность HTTP-кодов и заголовков", "core", "L1_technical", "http_status_ratio"),
    FactorSpec("F-TECH-003", "Выполнение JavaScript при обходе", "core", "L1_technical", "render_required_ratio"),
    FactorSpec("F-TECH-004", "Отсутствие избыточных дубликатов URL", "core", "L1_technical", "protocol_duplication"),
    FactorSpec("F-TECH-006", "Корректная structured data (JSON-LD)", "core", "L1_technical", "schema_hints_ratio"),
    FactorSpec("F-CONT-004", "Чёткая структура заголовков (H1–H6)", "core", "L2_content", "heading_structure_ratio"),
    FactorSpec("F-CONT-005", "E-E-A-T сигналы (Experience, Expertise, Authoritativeness, Trustworthiness)", "core", "L2_content", "trust_signal_ratio"),
    FactorSpec("F-CONT-007", "Ответ в начале блока (answer-first)", "core", "L2_content", "answer_ready_ratio"),
    FactorSpec("F-AEO-001", "Структура «вопрос → краткий ответ»", "core", "L2_content", "faq_ratio"),
    FactorSpec("F-SEM-001", "Тематическое покрытие (topical authority)", "core", "L3_semantic", "typed_page_ratio"),
    FactorSpec("F-SEM-003", "Явная привязка страницы к сущности (entity)", "core", "L3_semantic", "entity_signal_ratio"),
    FactorSpec("F-SEM-005", "Глубина клика от главной (до 3 кликов)", "core", "L3_semantic", "shallow_click_ratio"),
    FactorSpec("F-AIO-004", "Явные определения и однозначность формулировок", "core", "L5_ai_interpretability", "explicit_definition_ratio"),
    FactorSpec("F-AIO-005", "Структурированные блоки (таблицы, списки, BLUF)", "core", "L5_ai_interpretability", "structured_block_ratio"),
    FactorSpec("F-CONT-006", "Личный опыт и первичные материалы (Experience)", "extended", "L2_content", "proof_signal_ratio"),
    FactorSpec("F-KG-003", "Разметка Organization/LocalBusiness/Product/FAQ как слой семантических атрибутов", "extended", "L3_semantic", "kg_markup_ratio"),
    FactorSpec("F-AEO-006", "Короткие voice-ready answer-блоки (под ассистентов)", "extended", "L5_ai_interpretability", "voice_ready_ratio"),
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sync_manifest(package_dir: Path) -> None:
    manifest_path = package_dir / "manifest.json"
    manifest = load_json(manifest_path)
    manifest.setdefault("schema_versions", {})["legacy_factor_assessments"] = SCHEMA_VERSION
    files = manifest.setdefault("files", [])
    entry = {
        "path": "analysis/legacy_factor_assessments.json",
        "category": "analysis",
        "required": False,
        "schema": "legacy_factor_assessments",
        "checksum": sha256_file(package_dir / "analysis" / "legacy_factor_assessments.json"),
    }
    for index, item in enumerate(files):
        if item.get("path") == entry["path"]:
            files[index] = entry
            break
    else:
        files.append(entry)
    files.sort(key=lambda item: item.get("path", ""))
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def read_payloads(package_dir: Path) -> tuple[dict, dict, dict, dict, dict]:
    review_brief = load_json(package_dir / "exports" / "review_brief.json")
    entities = load_json(package_dir / "analysis" / "entities.json")
    page_blocks = load_json(package_dir / "analysis" / "page_blocks.json") if (package_dir / "analysis" / "page_blocks.json").exists() else {"pages": []}
    render_plan = load_json(package_dir / "render" / "render_plan.json") if (package_dir / "render" / "render_plan.json").exists() else {}
    fetch_log = load_json(package_dir / "crawl" / "fetch_log.json") if (package_dir / "crawl" / "fetch_log.json").exists() else {"entries": []}
    return review_brief, entities, page_blocks, render_plan, fetch_log


def collect_measurements(package_dir: Path) -> dict[str, dict]:
    review_brief, entities, page_blocks, render_plan, fetch_log = read_payloads(package_dir)
    pages = list(page_blocks.get("pages", []))
    technical_pages = list((package_dir / "pages" / "technical").glob("*.json"))
    technical_payloads = [load_json(path) for path in technical_pages]
    fetch_entries = list(fetch_log.get("entries", []))
    html_entries = [entry for entry in fetch_entries if str(entry.get("content_type", "")).startswith("text/html")]
    typed_pages = [
        entity for entity in entities.get("entities", [])
        if entity.get("type") == "page" and entity.get("attributes", {}).get("page_type") not in {"generic", "", None}
    ]
    schema_pages = 0
    entity_pages = 0
    heading_pages = 0
    for payload in technical_payloads:
        schema_hints = payload.get("schema_hints", [])
        if schema_hints:
            schema_pages += 1
            if any(str(item).strip() for item in schema_hints):
                entity_pages += 1
        headings = payload.get("headings", {}) or {}
        h1 = [str(item).strip() for item in headings.get("h1", []) if str(item).strip()]
        h2 = [str(item).strip() for item in headings.get("h2", []) if str(item).strip()]
        if h1 or h2:
            heading_pages += 1
    answer_ready_pages = 0
    faq_pages = 0
    structured_pages = 0
    trust_signal_pages = 0
    explicit_definition_pages = 0
    proof_signal_pages = 0
    for page in pages:
        block_map = {block.get("type"): bool(block.get("present")) for block in page.get("blocks", [])}
        if block_map.get("definition") or block_map.get("faq"):
            answer_ready_pages += 1
        if block_map.get("faq"):
            faq_pages += 1
        if block_map.get("definition"):
            explicit_definition_pages += 1
        if block_map.get("definition") or block_map.get("process_steps") or block_map.get("specs"):
            structured_pages += 1
        if block_map.get("proof") or block_map.get("legal_trust") or block_map.get("contacts"):
            trust_signal_pages += 1
        if block_map.get("proof") or block_map.get("specs") or block_map.get("availability") or block_map.get("fulfillment"):
            proof_signal_pages += 1
    total_pages = max(len(pages), len(technical_pages), int(review_brief.get("summary", {}).get("page_count", 0)))
    render_summary = render_plan.get("summary", {})
    successful_http_entries = [
        entry
        for entry in fetch_entries
        if entry.get("status") == "fetched" and 200 <= int(entry.get("status_code", 0) or 0) < 400
    ]
    shallow_click_entries = [entry for entry in html_entries if int(entry.get("depth", 99) or 99) <= 3]
    return {
        "http_status_ratio": {
            "value": ratio(len(successful_http_entries), max(len(fetch_entries), 1)) if fetch_entries else None,
            "notes": f"successful fetched URLs={len(successful_http_entries)} of {len(fetch_entries)}" if fetch_entries else "fetch log is missing",
        },
        "render_required_ratio": {
            "value": ratio(int(render_summary.get("render_required_count", 0)), max(int(render_summary.get("total_pages", 0)), 1)) if render_plan else None,
            "notes": f"render-required pages={render_summary.get('render_required_count', 0)} of {render_summary.get('total_pages', 0)}" if render_plan else "render plan is missing",
        },
        "protocol_duplication": {
            "value": 0.0 if not review_brief.get("crawl_quality", {}).get("protocol_duplication") else 1.0,
            "notes": "protocol duplication detected" if review_brief.get("crawl_quality", {}).get("protocol_duplication") else "no http/https duplication detected",
        },
        "schema_hints_ratio": {
            "value": ratio(schema_pages, max(len(technical_pages), 1)) if technical_pages else None,
            "notes": f"pages with schema hints={schema_pages} of {len(technical_pages)}" if technical_pages else "technical pages are missing",
        },
        "heading_structure_ratio": {
            "value": ratio(heading_pages, max(len(technical_pages), 1)) if technical_pages else None,
            "notes": f"pages with heading structure={heading_pages} of {len(technical_pages)}" if technical_pages else "technical pages are missing",
        },
        "trust_signal_ratio": {
            "value": ratio(trust_signal_pages, max(total_pages, 1)) if total_pages else None,
            "notes": f"pages with trust signals={trust_signal_pages} of {total_pages}",
        },
        "proof_signal_ratio": {
            "value": ratio(proof_signal_pages, max(total_pages, 1)) if total_pages else None,
            "notes": f"pages with proof/primary-material signals={proof_signal_pages} of {total_pages}",
        },
        "answer_ready_ratio": {
            "value": ratio(answer_ready_pages, max(total_pages, 1)) if total_pages else None,
            "notes": f"pages with definition/faq blocks={answer_ready_pages} of {total_pages}",
        },
        "faq_ratio": {
            "value": ratio(faq_pages, max(total_pages, 1)) if total_pages else None,
            "notes": f"pages with faq blocks={faq_pages} of {total_pages}",
        },
        "typed_page_ratio": {
            "value": ratio(len(typed_pages), max(len(entities.get('entities', [])), 1)) if entities.get("entities") else None,
            "notes": f"non-generic typed pages={len(typed_pages)} of {len(entities.get('entities', []))}",
        },
        "entity_signal_ratio": {
            "value": ratio(entity_pages, max(len(technical_pages), 1)) if technical_pages else None,
            "notes": f"pages with schema/entity hints={entity_pages} of {len(technical_pages)}" if technical_pages else "technical pages are missing",
        },
        "kg_markup_ratio": {
            "value": ratio(entity_pages, max(len(technical_pages), 1)) if technical_pages else None,
            "notes": f"pages with semantic markup attributes={entity_pages} of {len(technical_pages)}" if technical_pages else "technical pages are missing",
        },
        "shallow_click_ratio": {
            "value": ratio(len(shallow_click_entries), max(len(html_entries), 1)) if html_entries else None,
            "notes": f"html pages within 3 clicks={len(shallow_click_entries)} of {len(html_entries)}" if html_entries else "html fetch entries are missing",
        },
        "explicit_definition_ratio": {
            "value": ratio(explicit_definition_pages, max(total_pages, 1)) if total_pages else None,
            "notes": f"pages with explicit definition blocks={explicit_definition_pages} of {total_pages}",
        },
        "voice_ready_ratio": {
            "value": ratio(explicit_definition_pages, max(total_pages, 1)) if total_pages else None,
            "notes": f"pages with short answer-first style blocks={explicit_definition_pages} of {total_pages}",
        },
        "structured_block_ratio": {
            "value": ratio(structured_pages, max(total_pages, 1)) if total_pages else None,
            "notes": f"pages with structured blocks={structured_pages} of {total_pages}",
        },
    }


def factor_result(spec: FactorSpec, measure: dict) -> dict:
    value = measure.get("value")
    if value is None:
        return {
            "factor_id": spec.factor_id,
            "name": spec.name,
            "tier": spec.tier,
            "level": spec.level,
            "status": "unmeasured",
            "score": None,
            "measurement_key": spec.measure_key,
            "measurement_value": None,
            "summary": measure.get("notes", "measurement unavailable"),
        }
    if spec.measure_key == "protocol_duplication":
        score = 0.0 if value >= 1.0 else 1.0
    elif spec.measure_key == "http_status_ratio":
        score = 1.0 if value >= 0.95 else 0.5 if value >= 0.8 else 0.0
    elif spec.measure_key == "render_required_ratio":
        score = 1.0 if value <= 0.3 else 0.5 if value <= 0.6 else 0.0
    elif spec.measure_key == "schema_hints_ratio":
        score = 1.0 if value >= 0.4 else 0.5 if value >= 0.15 else 0.0
    elif spec.measure_key == "heading_structure_ratio":
        score = 1.0 if value >= 0.7 else 0.5 if value >= 0.4 else 0.0
    elif spec.measure_key == "trust_signal_ratio":
        score = 1.0 if value >= 0.5 else 0.5 if value >= 0.2 else 0.0
    elif spec.measure_key == "proof_signal_ratio":
        score = 1.0 if value >= 0.3 else 0.5 if value >= 0.1 else 0.0
    elif spec.measure_key == "answer_ready_ratio":
        score = 1.0 if value >= 0.3 else 0.5 if value >= 0.1 else 0.0
    elif spec.measure_key == "faq_ratio":
        score = 1.0 if value >= 0.3 else 0.5 if value >= 0.1 else 0.0
    elif spec.measure_key == "typed_page_ratio":
        score = 1.0 if value >= 0.5 else 0.5 if value >= 0.2 else 0.0
    elif spec.measure_key == "entity_signal_ratio":
        score = 1.0 if value >= 0.4 else 0.5 if value >= 0.15 else 0.0
    elif spec.measure_key == "kg_markup_ratio":
        score = 1.0 if value >= 0.4 else 0.5 if value >= 0.15 else 0.0
    elif spec.measure_key == "shallow_click_ratio":
        score = 1.0 if value >= 0.9 else 0.5 if value >= 0.7 else 0.0
    elif spec.measure_key == "explicit_definition_ratio":
        score = 1.0 if value >= 0.4 else 0.5 if value >= 0.15 else 0.0
    elif spec.measure_key == "voice_ready_ratio":
        score = 1.0 if value >= 0.3 else 0.5 if value >= 0.1 else 0.0
    elif spec.measure_key == "structured_block_ratio":
        score = 1.0 if value >= 0.5 else 0.5 if value >= 0.2 else 0.0
    else:
        score = 0.0
    status = "pass" if score >= 0.8 else "partial" if score >= 0.4 else "fail"
    return {
        "factor_id": spec.factor_id,
        "name": spec.name,
        "tier": spec.tier,
        "level": spec.level,
        "status": status,
        "score": score,
        "measurement_key": spec.measure_key,
        "measurement_value": value,
        "summary": measure.get("notes", ""),
    }


def build_payload(package_dir: Path) -> dict:
    manifest = load_json(package_dir / "manifest.json")
    measures = collect_measurements(package_dir)
    assessments = [factor_result(spec, measures[spec.measure_key]) for spec in FACTOR_SPECS]
    measured = [item for item in assessments if item["status"] != "unmeasured"]
    return {
        "schema_version": SCHEMA_VERSION,
        "audit_id": manifest["audit_id"],
        "source_method": "current_artifacts_to_legacy_factors_v1",
        "assessments": assessments,
        "summary": {
            "total_factors": len(assessments),
            "measured_factors": len(measured),
            "unmeasured_factors": len(assessments) - len(measured),
            "levels_covered": sorted({item["level"] for item in measured}),
        },
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 scripts/build_legacy_factor_assessments.py <audit_package_dir>", file=sys.stderr)
        return 1
    package_dir = Path(argv[1])
    issues = ensure_approved(package_dir)
    if issues:
        print("legacy factor assessment generation blocked", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1
    analysis_dir = package_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    payload = build_payload(package_dir)
    (analysis_dir / "legacy_factor_assessments.json").write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    sync_manifest(package_dir)
    print("legacy factor assessments generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
