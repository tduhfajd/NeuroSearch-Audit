#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from python.common.validators import validate_contracts, validate_evidence, validate_prompts


SCHEMA_VERSION = "1.0.0"
METHODOLOGY_REFERENCE = "legacy_scoring_weights_v0_2"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sync_manifest_scoring_parity_snapshot(package_dir: Path) -> None:
    manifest_path = package_dir / "manifest.json"
    manifest = load_json(manifest_path)
    manifest.setdefault("schema_versions", {})["scoring_parity_snapshot"] = SCHEMA_VERSION
    files = manifest.setdefault("files", [])
    entry = {
        "path": "exports/scoring_parity_snapshot.json",
        "category": "export",
        "required": False,
        "schema": "scoring_parity_snapshot",
        "checksum": sha256_file(package_dir / "exports" / "scoring_parity_snapshot.json"),
    }
    for index, item in enumerate(files):
        if item.get("path") == entry["path"]:
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


def summarize_package_signals(package_dir: Path) -> dict[str, int]:
    facts = load_json(package_dir / "analysis/normalized_facts.json")
    technical_pages = list((package_dir / "pages/technical").glob("*.json"))
    render_pages = list((package_dir / "pages/rendered").glob("*.json"))
    fetch_log = load_json(package_dir / "crawl/fetch_log.json")

    block_presence_count = 0
    factual_count = 0
    fact_types: set[str] = set()
    for item in facts.get("facts", []):
        fact_type = str(item.get("fact_type", ""))
        fact_types.add(fact_type)
        if fact_type == "block_presence":
            block_presence_count += 1
        elif fact_type != "page_type":
            factual_count += 1

    schema_hint_pages = 0
    transport_pages = 0
    for path in technical_pages:
        payload = load_json(path)
        if payload.get("schema_hints"):
            schema_hint_pages += 1
        if payload.get("transport_signals"):
            transport_pages += 1

    return {
        "technical_pages": len(technical_pages),
        "rendered_pages": len(render_pages),
        "fetched_entries": len(fetch_log.get("entries", [])),
        "block_presence_count": block_presence_count,
        "factual_count": factual_count,
        "schema_hint_pages": schema_hint_pages,
        "transport_pages": transport_pages,
        "has_contact_facts": int("contact_phone" in fact_types or "contact_email" in fact_types),
        "has_payment_facts": int("payment_option" in fact_types),
        "has_legal_facts": int("legal_hint" in fact_types),
        "has_transport_facts": int("transport_policy" in fact_types),
    }


def build_snapshot(package_dir: Path) -> dict:
    manifest = load_json(package_dir / "manifest.json")
    summary = summarize_package_signals(package_dir)

    levels = [
        {
            "level": "L1_technical",
            "status": "partial",
            "current_signals": [
                "crawl fetch status and content types",
                "technical page extraction",
                "canonical and robots extraction",
                "transport security signals",
                "render-aware runtime slice",
            ],
            "missing_legacy_capabilities": [
                "core web vitals",
                "server-speed scoring",
                "duplicate clustering as a score input",
                "broad js execution parity scoring",
            ],
        },
        {
            "level": "L2_content",
            "status": "partial" if summary["block_presence_count"] > 0 else "not_measured",
            "current_signals": [
                "deterministic block presence",
                "faq/proof/pricing/terms/process coverage",
                "page-family content expectations",
            ],
            "missing_legacy_capabilities": [
                "answer-length quality checks",
                "freshness and update scoring",
                "e-e-a-t style content evidence scoring",
                "clickbait and fact-check scoring",
            ],
        },
        {
            "level": "L3_semantic",
            "status": "partial" if summary["factual_count"] > 0 or summary["schema_hint_pages"] > 0 else "not_measured",
            "current_signals": [
                "page typing",
                "schema hint extraction",
                "contact/payment/legal factual signals",
                "coverage by business page family",
            ],
            "missing_legacy_capabilities": [
                "external vertical consistency",
                "entity graph consistency across channels",
                "canonical entity-page modeling",
            ],
        },
        {
            "level": "L4_behavioral",
            "status": "not_measured",
            "current_signals": [],
            "missing_legacy_capabilities": [
                "ctr by query clusters",
                "dwell or satisfaction signals",
                "conversion events from analytics and search traffic",
            ],
        },
        {
            "level": "L5_ai_interpretability",
            "status": "partial" if summary["block_presence_count"] > 0 else "not_measured",
            "current_signals": [
                "faq and answer-shaped blocks",
                "structured block extraction",
                "protocol and canonical safety signals",
                "render-aware extraction for thin and dynamic pages",
            ],
            "missing_legacy_capabilities": [
                "citation accuracy",
                "extraction stability under repeated prompts",
                "llms.txt and ai-specific integration signals",
                "feed and api readiness scoring",
            ],
        },
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "audit_id": manifest["audit_id"],
        "methodology_reference": METHODOLOGY_REFERENCE,
        "overall_status": "partial",
        "levels": levels,
        "notes": [
            "Current report delivery is already migrated, but current score semantics are not yet legacy-equivalent.",
            "This snapshot describes methodology coverage only; it does not claim score parity with legacy NeuroSearch.",
        ],
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 scripts/build_scoring_parity_snapshot.py <audit_package_dir>", file=sys.stderr)
        return 1

    package_dir = Path(argv[1])
    issues = ensure_approved(package_dir)
    if issues:
        print("scoring parity snapshot generation blocked", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    exports_dir = package_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    payload = build_snapshot(package_dir)
    (exports_dir / "scoring_parity_snapshot.json").write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    sync_manifest_scoring_parity_snapshot(package_dir)
    print("scoring parity snapshot generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

