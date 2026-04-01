from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys


def write_case(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_diff_benchmark_cases_reports_added_removed_and_modified(tmp_path: Path) -> None:
    before_dir = tmp_path / "before"
    after_dir = tmp_path / "after"
    before_dir.mkdir()
    after_dir.mkdir()

    write_case(
        before_dir / "service_case.json",
        {
            "schema_version": "1.0.0",
            "case_id": "service_case",
            "segment": "service",
            "page_type": "service",
            "source_fixture": "fixture-a.json",
            "expected_signals": {"manual_tax_level": "medium", "fit_assessment": "good", "top_gap_focus": ["pricing"]},
            "calibration_notes": ["before"],
        },
    )
    write_case(
        before_dir / "removed_case.json",
        {
            "schema_version": "1.0.0",
            "case_id": "removed_case",
            "segment": "content",
            "page_type": "article",
            "source_fixture": "fixture-b.json",
            "expected_signals": {"manual_tax_level": "low", "fit_assessment": "good", "top_gap_focus": ["definition"]},
            "calibration_notes": ["removed"],
        },
    )

    write_case(
        after_dir / "service_case.json",
        {
            "schema_version": "1.0.0",
            "case_id": "service_case",
            "segment": "service",
            "page_type": "service",
            "source_fixture": "fixture-a.json",
            "expected_signals": {"manual_tax_level": "high", "fit_assessment": "acceptable_with_gaps", "top_gap_focus": ["pricing", "contacts"]},
            "calibration_notes": ["after"],
        },
    )
    write_case(
        after_dir / "added_case.json",
        {
            "schema_version": "1.0.0",
            "case_id": "added_case",
            "segment": "commercial",
            "page_type": "product",
            "source_fixture": "fixture-c.json",
            "expected_signals": {"manual_tax_level": "high", "fit_assessment": "acceptable_with_gaps", "top_gap_focus": ["proof"]},
            "calibration_notes": ["added"],
        },
    )

    result = subprocess.run(
        [sys.executable, "scripts/diff_benchmark_cases.py", str(before_dir), str(after_dir)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "benchmark diff summary" in result.stdout
    payload = json.loads(result.stdout.split("\n", 1)[1])
    assert payload["changed_case_count"] == 3
    changes = {item["case_id"]: item["change"] for item in payload["diffs"]}
    assert changes["added_case"] == "added"
    assert changes["removed_case"] == "removed"
    assert changes["service_case"] == "modified"


def test_diff_benchmark_cases_detects_snapshot_content_drift(tmp_path: Path) -> None:
    before_dir = tmp_path / "before"
    after_dir = tmp_path / "after"
    before_dir.mkdir()
    after_dir.mkdir()

    before_snapshot = tmp_path / "before_snapshot.json"
    after_snapshot = tmp_path / "after_snapshot.json"
    before_snapshot.write_text('{"top_gaps":["proof"]}\n', encoding="utf-8")
    after_snapshot.write_text('{"top_gaps":["terms"]}\n', encoding="utf-8")

    before_case = {
        "schema_version": "1.0.0",
        "case_id": "service_case",
        "segment": "service",
        "page_type": "service",
        "source_fixture": str(before_snapshot),
        "expected_signals": {"manual_tax_level": "medium", "fit_assessment": "good", "top_gap_focus": ["proof"]},
        "calibration_notes": ["before"],
    }
    after_case = dict(before_case)
    after_case["source_fixture"] = str(after_snapshot)

    write_case(before_dir / "service_case.json", before_case)
    write_case(after_dir / "service_case.json", after_case)

    result = subprocess.run(
        [sys.executable, "scripts/diff_benchmark_cases.py", str(before_dir), str(after_dir)],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout.split("\n", 1)[1])
    modified = payload["diffs"][0]
    assert modified["change"] == "modified"
    assert "source_fixture_digest" in modified["fields"]
