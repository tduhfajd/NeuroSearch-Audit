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


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sync_manifest_exports(package_dir: Path) -> None:
    manifest_path = package_dir / "manifest.json"
    manifest = load_json(manifest_path)
    files = manifest.setdefault("files", [])
    manifest.setdefault("schema_versions", {})["export_summary"] = "1.0.0"
    manifest.setdefault("schema_versions", {})["export_backlog"] = "1.0.0"

    desired_entries = {
        "exports/summary.json": {
            "path": "exports/summary.json",
            "category": "export",
            "required": False,
            "schema": "export_summary",
            "checksum": sha256_file(package_dir / "exports" / "summary.json"),
        },
        "exports/backlog.json": {
            "path": "exports/backlog.json",
            "category": "export",
            "required": False,
            "schema": "export_backlog",
            "checksum": sha256_file(package_dir / "exports" / "backlog.json"),
        },
    }

    indexed = {entry.get("path"): idx for idx, entry in enumerate(files)}
    for path, entry in desired_entries.items():
        if path in indexed:
            files[indexed[path]] = entry
        else:
            files.append(entry)
    files.sort(key=lambda item: item.get("path", ""))
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def export_summary(package_dir: Path) -> dict:
    manifest = load_json(package_dir / "manifest.json")
    scores = load_json(package_dir / "analysis/ai_readiness_scores.json")
    contradictions = load_json(package_dir / "analysis/contradictions.json")

    validate_status = manifest.get("stage_status", {}).get("validate")
    return {
        "audit_id": manifest["audit_id"],
        "status": manifest["stage_status"],
        "lead_value_index": scores.get("lead_value_index", 0),
        "top_gaps": scores.get("top_gaps", []),
        "high_contradictions": [
            item["contradiction_id"]
            for item in contradictions.get("contradictions", [])
            if item.get("severity") == "high"
        ],
        "package_status": "approved" if validate_status == "completed" else "pending",
    }


def export_backlog(package_dir: Path) -> dict:
    recommendations = load_json(package_dir / "analysis/recommendations.json")
    audit_id = recommendations["audit_id"]
    return {
        "audit_id": audit_id,
        "items": [
            {
                "recommendation_id": item["recommendation_id"],
                "priority": item["priority"],
                "expected_impact": item["expected_impact"],
                "acceptance_criteria": item["acceptance_criteria"],
                "related_findings": item["related_findings"],
            }
            for item in recommendations.get("recommendations", [])
        ],
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 scripts/export_package.py <audit_package_dir>", file=sys.stderr)
        return 1

    package_dir = Path(argv[1])
    issues = validate_contracts(
        package_dir,
        ignored_paths=("exports/summary.json", "exports/backlog.json", "exports/review_brief.json"),
    ) + validate_evidence(package_dir) + validate_prompts(package_dir)
    manifest = load_json(package_dir / "manifest.json")
    if manifest.get("stage_status", {}).get("validate") != "completed":
        issues.append("package validate stage is not completed")
    if issues:
        print("package exports blocked", file=sys.stderr)
        for issue in issues:
            if isinstance(issue, str):
                print(f"- {issue}", file=sys.stderr)
            else:
                print(f"- {issue.path}: {issue.message}", file=sys.stderr)
        return 1

    exports_dir = package_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)

    summary = export_summary(package_dir)
    backlog = export_backlog(package_dir)

    (exports_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    (exports_dir / "backlog.json").write_text(json.dumps(backlog, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    sync_manifest_exports(package_dir)

    print("package exports generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
