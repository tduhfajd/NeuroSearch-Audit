#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_client_report_bundle import main as build_client_report_bundle_main
from scripts.build_legacy_factor_assessments import main as build_legacy_factor_assessments_main
from scripts.build_legacy_index_scores import main as build_legacy_index_scores_main
from scripts.export_package import main as export_package_main
from scripts.generate_commercial_documents import main as generate_commercial_documents_main
from scripts.generate_expert_report import main as generate_expert_report_main
from scripts.generate_internal_technical_report import main as generate_internal_technical_report_main
from scripts.generate_review_artifacts import main as generate_review_artifacts_main
from scripts.generate_technical_client_report import main as generate_technical_client_report_main


DERIVED_RELATIVE_PATHS = (
    "exports/review_brief.json",
    "exports/review_brief.md",
    "exports/summary.json",
    "exports/backlog.json",
    "exports/client_report_input.json",
    "exports/client_report.json",
    "exports/client_report.md",
    "exports/expert_report.json",
    "exports/expert_report.md",
    "exports/technical_client_report.json",
    "exports/technical_client_report.md",
    "exports/internal_technical_report.md",
    "exports/commercial_offer.json",
    "exports/commercial_offer.md",
    "exports/technical_action_plan.json",
    "exports/technical_action_plan.md",
    "analysis/legacy_factor_assessments.json",
    "analysis/legacy_index_scores.json",
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish one audit run into project-root out/")
    parser.add_argument("--artifact-root", required=True, help="Root containing audit_package/ and runtime/")
    parser.add_argument("--audit-id", required=True, help="Audit identifier")
    parser.add_argument("--project-root", default=str(ROOT), help="Project root where out/ should be created")
    parser.add_argument("--brand", help="Optional path to custom brand.yml")
    return parser.parse_args(argv[1:])


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip())
    return cleaned.strip("-_.") or "site"


def run_dir_name(audit_id: str, domain: str) -> str:
    normalized_audit = audit_id.removeprefix("aud_")
    return f"{normalized_audit}-{safe_name(domain)}"


def package_dir(artifact_root: Path, audit_id: str) -> Path:
    return artifact_root / "audit_package" / audit_id


def runtime_dir(artifact_root: Path, audit_id: str) -> Path:
    return artifact_root / "runtime" / audit_id


def clean_derived_artifacts(pkg_dir: Path) -> None:
    for relative in DERIVED_RELATIVE_PATHS:
        path = pkg_dir / relative
        if path.exists():
            path.unlink()


def run_step(name: str, fn, argv: list[str]) -> None:
    exit_code = fn(argv)
    if exit_code != 0:
        raise RuntimeError(f"{name} failed with exit code {exit_code}")


def ensure_documents(pkg_dir: Path, bundle_dir: Path, brand_path: Path | None = None) -> None:
    clean_derived_artifacts(pkg_dir)
    run_step("generate_review_artifacts", generate_review_artifacts_main, ["generate_review_artifacts.py", str(pkg_dir)])
    run_step("export_package", export_package_main, ["export_package.py", str(pkg_dir)])
    run_step(
        "build_legacy_factor_assessments",
        build_legacy_factor_assessments_main,
        ["build_legacy_factor_assessments.py", str(pkg_dir)],
    )
    run_step(
        "build_legacy_index_scores",
        build_legacy_index_scores_main,
        ["build_legacy_index_scores.py", str(pkg_dir)],
    )
    run_step("generate_expert_report", generate_expert_report_main, ["generate_expert_report.py", str(pkg_dir)])
    run_step(
        "generate_technical_client_report",
        generate_technical_client_report_main,
        ["generate_technical_client_report.py", str(pkg_dir)],
    )
    run_step(
        "generate_internal_technical_report",
        generate_internal_technical_report_main,
        ["generate_internal_technical_report.py", str(pkg_dir)],
    )
    run_step(
        "generate_commercial_documents",
        generate_commercial_documents_main,
        ["generate_commercial_documents.py", str(pkg_dir)],
    )
    run_step(
        "build_client_report_bundle",
        build_client_report_bundle_main,
        [
            "build_client_report_bundle.py",
            str(pkg_dir),
            "--output-dir",
            str(bundle_dir),
            *(["--brand", str(brand_path)] if brand_path else []),
        ],
    )


def copy_tree_if_exists(source: Path, target: Path) -> None:
    if not source.exists():
        return
    shutil.copytree(source, target, dirs_exist_ok=True)


def publish_latest_reports(run_dir: Path, audit_id: str, project_root: Path, domain: str) -> None:
    latest_dir = project_root / "latest_reports"
    if latest_dir.exists():
        shutil.rmtree(latest_dir)
    latest_dir.mkdir(parents=True, exist_ok=True)

    bundle_dir = run_dir / "deliverables" / "client-report"
    exports_dir = run_dir / "audit_package" / audit_id / "exports"
    safe_domain = safe_name(domain)
    report_base = f"report_{domain}"

    files_to_copy = [
        (bundle_dir / f"{report_base}.pdf", latest_dir / f"client_report_{safe_domain}.pdf"),
        (bundle_dir / f"{report_base}.html", latest_dir / f"client_report_{safe_domain}.html"),
        (bundle_dir / f"{report_base}.docx", latest_dir / f"client_report_{safe_domain}.docx"),
        (bundle_dir / f"{report_base}.md", latest_dir / f"client_report_{safe_domain}.md"),
        (exports_dir / "internal_technical_report.md", latest_dir / f"internal_technical_report_{safe_domain}.md"),
    ]
    for source, target in files_to_copy:
        if source.exists():
            shutil.copy2(source, target)

    payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "domain": domain,
        "run_dir": str(run_dir),
        "published_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    (latest_dir / "RUN_INFO.json").write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_snapshot_metadata(run_dir: Path, artifact_root: Path, audit_id: str, domain: str) -> None:
    payload = {
        "schema_version": "1.0.0",
        "audit_id": audit_id,
        "domain": domain,
        "source_artifact_root": str(artifact_root),
        "published_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    (run_dir / "run_snapshot.json").write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def publish_run(artifact_root: Path, audit_id: str, project_root: Path, brand_path: Path | None = None) -> Path:
    pkg_dir = package_dir(artifact_root, audit_id)
    if not pkg_dir.exists():
        raise FileNotFoundError(f"audit package not found: {pkg_dir}")

    bundle_input = pkg_dir / "exports" / "client_report_input.json"
    domain = audit_id
    if bundle_input.exists():
        domain = load_json(bundle_input).get("site", {}).get("primary_domain", audit_id) or audit_id
    else:
        entities = load_json(pkg_dir / "analysis" / "entities.json")
        for entity in entities.get("entities", []):
            label = str(entity.get("label", ""))
            if entity.get("type") == "page" and label:
                domain = safe_name(label.split("/")[2] if "://" in label else label)
                break

    run_dir = project_root / "out" / run_dir_name(audit_id, domain)
    if run_dir.exists():
        shutil.rmtree(run_dir)
    bundle_dir = run_dir / "deliverables" / "client-report"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    ensure_documents(pkg_dir, bundle_dir, brand_path=brand_path)
    copy_tree_if_exists(pkg_dir, run_dir / "audit_package" / audit_id)
    copy_tree_if_exists(runtime_dir(artifact_root, audit_id), run_dir / "runtime" / audit_id)
    write_snapshot_metadata(run_dir, artifact_root, audit_id, domain)
    publish_latest_reports(run_dir, audit_id, project_root, domain)
    return run_dir


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    run_dir = publish_run(
        Path(args.artifact_root),
        args.audit_id,
        Path(args.project_root),
        brand_path=Path(args.brand).resolve() if args.brand else None,
    )
    print(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
