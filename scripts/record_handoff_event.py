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


ALLOWED_EVENT_TYPES = {
    "package_approved",
    "review_prepared",
    "ai_handoff_sent",
    "post_handoff_captured",
}


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


def output_root_for(package_dir: Path) -> Path:
    return package_dir.parent.parent


def handoff_dir_for(package_dir: Path) -> Path:
    audit_id = package_dir.name
    return output_root_for(package_dir) / "handoff" / audit_id


def event_timestamp(raw: str | None) -> str:
    if raw:
        return raw
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def event_id_for(timestamp: str, event_type: str) -> str:
    slug = (
        timestamp.replace("-", "")
        .replace(":", "")
        .replace("T", "T")
        .replace("Z", "Z")
    )
    return f"evt_{slug}_{event_type}"


def main(argv: list[str]) -> int:
    parser = ArgumentParser()
    parser.add_argument("package_dir")
    parser.add_argument("--event-type", required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--artifact", action="append", default=[])
    parser.add_argument("--notes", default="")
    parser.add_argument("--timestamp", default="")
    args = parser.parse_args(argv[1:])

    if args.event_type not in ALLOWED_EVENT_TYPES:
        print(f"unsupported event type: {args.event_type}", file=sys.stderr)
        return 1

    package_dir = Path(args.package_dir)
    issues = ensure_approved(package_dir)
    if issues:
        print("handoff event blocked", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    manifest = load_json(package_dir / "manifest.json")
    timestamp = event_timestamp(args.timestamp or None)
    event = {
        "event_id": event_id_for(timestamp, args.event_type),
        "audit_id": manifest["audit_id"],
        "timestamp": timestamp,
        "event_type": args.event_type,
        "actor": args.actor,
        "artifacts": sorted(args.artifact),
        "notes": args.notes,
    }

    handoff_dir = handoff_dir_for(package_dir)
    handoff_dir.mkdir(parents=True, exist_ok=True)
    log_path = handoff_dir / "handoff_log.jsonl"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True) + "\n")

    print("handoff event recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
