#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_client_report_input import ensure_approved, load_json
from scripts.build_legacy_factor_assessments import main as build_factor_main


SCHEMA_VERSION = "1.0.0"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    total = sum(weights.values())
    if total <= 0:
        return {key: 0.0 for key in weights}
    return {key: value / total for key, value in weights.items()}


def sync_manifest(package_dir: Path) -> None:
    manifest_path = package_dir / "manifest.json"
    manifest = load_json(manifest_path)
    manifest.setdefault("schema_versions", {})["legacy_index_scores"] = SCHEMA_VERSION
    files = manifest.setdefault("files", [])
    entry = {
        "path": "analysis/legacy_index_scores.json",
        "category": "analysis",
        "required": False,
        "schema": "legacy_index_scores",
        "checksum": sha256_file(package_dir / "analysis" / "legacy_index_scores.json"),
    }
    for index, item in enumerate(files):
        if item.get("path") == entry["path"]:
            files[index] = entry
            break
    else:
        files.append(entry)
    files.sort(key=lambda item: item.get("path", ""))
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def ensure_factor_assessments(package_dir: Path) -> None:
    path = package_dir / "analysis" / "legacy_factor_assessments.json"
    if path.exists():
        return
    exit_code = build_factor_main(["build_legacy_factor_assessments.py", str(package_dir)])
    if exit_code != 0:
        raise RuntimeError("legacy factor assessments must be generated before legacy scores")


def score_index(index_cfg: dict, factor_scores: list[dict], missing_policy: dict) -> tuple[float, dict]:
    tier_weights = {key: float(value) for key, value in (index_cfg.get("tier_weights") or {}).items()}
    level_weights = {key: float(value) for key, value in (index_cfg.get("weights_by_level") or {}).items()}
    tier_scores: dict[str, float] = {}
    tier_breakdown: dict[str, dict] = {}
    measured_tiers: set[str] = set()
    for tier_name in tier_weights:
        level_scores: dict[str, float] = {}
        for level_name, level_weight in level_weights.items():
            if level_weight <= 0:
                continue
            scores = [float(item["score"]) for item in factor_scores if item["tier"] == tier_name and item["level"] == level_name and item["score"] is not None]
            if scores:
                level_scores[level_name] = sum(scores) / len(scores)
        if not level_scores:
            continue
        measured_tiers.add(tier_name)
        if missing_policy.get("levels") == "renormalize":
            effective_level_weights = normalize_weights({key: level_weights[key] for key in level_scores})
        else:
            effective_level_weights = {key: level_weights.get(key, 0.0) for key in level_scores}
        tier_score = sum(effective_level_weights[level] * value for level, value in level_scores.items())
        tier_scores[tier_name] = tier_score
        tier_breakdown[tier_name] = {"level_scores": level_scores, "effective_level_weights": effective_level_weights}
    if not tier_scores:
        return 0.0, {"tiers": {}, "effective_tier_weights": {}}
    effective_tier_weights = dict(tier_weights)
    if missing_policy.get("tiers") == "ignore_unmeasured":
        effective_tier_weights = normalize_weights({key: tier_weights[key] for key in measured_tiers})
    else:
        effective_tier_weights = normalize_weights(effective_tier_weights)
    total = sum(effective_tier_weights.get(tier, 0.0) * score for tier, score in tier_scores.items())
    return round(total, 4), {"tiers": tier_breakdown, "effective_tier_weights": effective_tier_weights}


def build_payload(package_dir: Path) -> dict:
    assessments_doc = load_json(package_dir / "analysis" / "legacy_factor_assessments.json")
    with (ROOT / "config" / "legacy_scoring_weights.yml").open("r", encoding="utf-8") as handle:
        weights = yaml.safe_load(handle) or {}
    missing_policy = weights.get("missing_data_policy") or {"levels": "renormalize", "tiers": "ignore_unmeasured"}
    scores: dict[str, dict] = {}
    for index_name, index_cfg in (weights.get("indices") or {}).items():
        score, breakdown = score_index(index_cfg, assessments_doc.get("assessments", []), missing_policy)
        scores[index_name] = {
            "score": score,
            "description": index_cfg.get("description", ""),
            "coverage": {
                "measured_factor_count": assessments_doc.get("summary", {}).get("measured_factors", 0),
                "total_factor_count": assessments_doc.get("summary", {}).get("total_factors", 0),
                "levels_covered": assessments_doc.get("summary", {}).get("levels_covered", []),
            },
            "breakdown": breakdown,
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "audit_id": assessments_doc["audit_id"],
        "weights_version": str(weights.get("version", "0.0")),
        "missing_data_policy": missing_policy,
        "indices": scores,
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 scripts/build_legacy_index_scores.py <audit_package_dir>", file=sys.stderr)
        return 1
    package_dir = Path(argv[1])
    issues = ensure_approved(package_dir)
    if issues:
        print("legacy index score generation blocked", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1
    ensure_factor_assessments(package_dir)
    payload = build_payload(package_dir)
    analysis_dir = package_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "legacy_index_scores.json").write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    sync_manifest(package_dir)
    print("legacy index scores generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
