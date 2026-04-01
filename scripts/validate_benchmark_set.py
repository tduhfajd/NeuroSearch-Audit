#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_DIR = ROOT / "testdata" / "fixtures" / "benchmark"

REQUIRED_FIELDS = {
    "schema_version",
    "case_id",
    "segment",
    "page_type",
    "source_fixture",
    "expected_signals",
    "calibration_notes",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_source_fixture(path: Path, payload: dict) -> str | None:
    if path.suffix != ".json":
        return None
    try:
        fixture = load_json(path)
    except json.JSONDecodeError as err:
        return f"{path}: invalid json fixture: {err}"

    if path.name.endswith("review_brief.snapshot.json"):
        top_gap_focus = payload.get("expected_signals", {}).get("top_gap_focus", [])
        snapshot_gaps = set(fixture.get("top_gaps", []))
        snapshot_focus = {
            gap
            for item in fixture.get("focus_areas", [])
            for gap in item.get("top_missing", [])
        }
        if not top_gap_focus:
            return f"{path}: review snapshot benchmark must declare top_gap_focus"
        if not any(gap in snapshot_gaps or gap in snapshot_focus for gap in top_gap_focus):
            return f"{path}: snapshot does not reflect expected top_gap_focus {top_gap_focus}"
    return None


def main() -> int:
    if not BENCHMARK_DIR.exists():
        print("benchmark validation failed")
        print("- benchmark directory is missing")
        return 1

    case_paths = sorted(BENCHMARK_DIR.glob("*_case.json"))
    if len(case_paths) < 4:
        print("benchmark validation failed")
        print("- benchmark set must contain at least four cases")
        return 1

    seen_segments: set[str] = set()
    seen_page_types: set[str] = set()
    for path in case_paths:
        payload = load_json(path)
        missing = sorted(REQUIRED_FIELDS - set(payload.keys()))
        if missing:
            print("benchmark validation failed")
            print(f"- {path}: missing fields {missing}")
            return 1
        source_fixture = ROOT / payload["source_fixture"]
        if not source_fixture.exists():
            print("benchmark validation failed")
            print(f"- {path}: source fixture does not exist: {payload['source_fixture']}")
            return 1
        fixture_issue = validate_source_fixture(source_fixture, payload)
        if fixture_issue is not None:
            print("benchmark validation failed")
            print(f"- {fixture_issue}")
            return 1
        seen_segments.add(payload["segment"])
        seen_page_types.add(payload["page_type"])

    if len(seen_segments) < 2:
        print("benchmark validation failed")
        print("- benchmark set must cover at least two segments")
        return 1
    if len(seen_page_types) < 2:
        print("benchmark validation failed")
        print("- benchmark set must cover at least two page types")
        return 1
    if "commercial" not in seen_segments:
        print("benchmark validation failed")
        print("- benchmark set must include at least one commercial case")
        return 1

    print("benchmark validation passed")
    print(json.dumps({
        "cases": len(case_paths),
        "segments": sorted(seen_segments),
        "page_types": sorted(seen_page_types),
    }, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
