#!/usr/bin/env python3
from __future__ import annotations

from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from python.common.validators import validate_contracts, validate_evidence, validate_prompts


SCHEMA_VERSION = "1.0.0"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_approved(package_dir: Path) -> list[str]:
    issues = validate_contracts(package_dir) + validate_evidence(package_dir) + validate_prompts(package_dir)
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


def handoff_dir_for(package_dir: Path) -> Path:
    return package_dir.parent.parent / "handoff" / package_dir.name


def artifact_list(package_dir: Path) -> list[str]:
    exports_dir = package_dir / "exports"
    if not exports_dir.exists():
        return []
    return sorted(
        str(path.relative_to(package_dir))
        for path in exports_dir.iterdir()
        if path.is_file() and path.name != ".gitkeep"
    )


def handoff_event_types(handoff_dir: Path) -> list[str]:
    log_path = handoff_dir / "handoff_log.jsonl"
    if not log_path.exists():
        return []
    event_types: list[str] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        event_types.append(payload["event_type"])
    return event_types


def tax_level(value: int, low_max: int, medium_max: int) -> str:
    if value <= low_max:
        return "low"
    if value <= medium_max:
        return "medium"
    return "high"


def fit_assessment(manual_steps: int, reformatting_steps: int, missing_exports: list[str], complaints: list[str]) -> str:
    if manual_steps <= 2 and reformatting_steps <= 1 and not missing_exports and not complaints:
        return "good"
    if manual_steps >= 6 or reformatting_steps >= 4 or len(missing_exports) >= 2:
        return "poor"
    return "acceptable_with_gaps"


def main(argv: list[str]) -> int:
    parser = ArgumentParser()
    parser.add_argument("package_dir")
    parser.add_argument("--manual-steps", type=int, default=0)
    parser.add_argument("--reformatting-steps", type=int, default=0)
    parser.add_argument("--missing-export", action="append", default=[])
    parser.add_argument("--complaint", action="append", default=[])
    parser.add_argument("--crm-signal", choices=["none", "weak", "strong"], default="none")
    parser.add_argument("--task-tracker-signal", choices=["none", "weak", "strong"], default="none")
    parser.add_argument("--direct-handoff-signal", choices=["none", "weak", "strong"], default="none")
    parser.add_argument("--recorded-at", default="")
    args = parser.parse_args(argv[1:])

    package_dir = Path(args.package_dir)
    issues = ensure_approved(package_dir)
    if issues:
        print("delivery friction capture blocked", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    manifest = load_json(package_dir / "manifest.json")
    handoff_dir = handoff_dir_for(package_dir)
    handoff_dir.mkdir(parents=True, exist_ok=True)

    recorded_at = args.recorded_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    missing_exports = sorted(args.missing_export)
    complaints = list(args.complaint)
    report = {
        "schema_version": SCHEMA_VERSION,
        "audit_id": manifest["audit_id"],
        "recorded_at": recorded_at,
        "review_artifacts": artifact_list(package_dir),
        "handoff_events": handoff_event_types(handoff_dir),
        "manual_steps": args.manual_steps,
        "reformatting_steps": args.reformatting_steps,
        "missing_exports": missing_exports,
        "operator_complaints": complaints,
        "integration_signals": {
            "crm_signal": args.crm_signal,
            "task_tracker_signal": args.task_tracker_signal,
            "direct_handoff_signal": args.direct_handoff_signal,
        },
        "summary": {
            "manual_tax_level": tax_level(args.manual_steps, 2, 5),
            "reformatting_tax_level": tax_level(args.reformatting_steps, 1, 3),
            "fit_assessment": fit_assessment(args.manual_steps, args.reformatting_steps, missing_exports, complaints),
        },
    }

    report_path = handoff_dir / "delivery_friction_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print("delivery friction report captured")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
