#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys
import hashlib


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fixture_digest(case_root: Path, source_fixture: str) -> str:
    path = Path(source_fixture)
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists():
        return "missing"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_case_set(root: Path) -> dict[str, dict]:
    cases: dict[str, dict] = {}
    for path in sorted(root.glob("*_case.json")):
        payload = load_json(path)
        payload["_source_fixture_digest"] = fixture_digest(root, payload["source_fixture"])
        cases[payload["case_id"]] = payload
    return cases


def summarize_case_diff(case_id: str, before: dict | None, after: dict | None) -> dict:
    if before is None:
        return {"case_id": case_id, "change": "added"}
    if after is None:
        return {"case_id": case_id, "change": "removed"}

    diff: dict[str, object] = {"case_id": case_id, "change": "modified", "fields": {}}
    fields: dict[str, object] = {}
    for key in ("segment", "page_type", "source_fixture", "expected_signals", "calibration_notes", "_source_fixture_digest"):
        if before.get(key) != after.get(key):
            label = "source_fixture_digest" if key == "_source_fixture_digest" else key
            fields[label] = {"before": before.get(key), "after": after.get(key)}
    if not fields:
        return {"case_id": case_id, "change": "unchanged"}
    diff["fields"] = fields
    return diff


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: diff_benchmark_cases.py <before_dir> <after_dir>")
        return 1

    before_dir = Path(argv[1]).resolve()
    after_dir = Path(argv[2]).resolve()
    if not before_dir.exists() or not after_dir.exists():
        print("benchmark diff failed")
        print("- both directories must exist")
        return 1

    before_cases = load_case_set(before_dir)
    after_cases = load_case_set(after_dir)
    case_ids = sorted(set(before_cases) | set(after_cases))

    diffs = [
        summarize_case_diff(case_id, before_cases.get(case_id), after_cases.get(case_id))
        for case_id in case_ids
    ]
    changed = [item for item in diffs if item["change"] != "unchanged"]

    print("benchmark diff summary")
    print(json.dumps(
        {
            "before_case_count": len(before_cases),
            "after_case_count": len(after_cases),
            "changed_case_count": len(changed),
            "diffs": changed,
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
