from __future__ import annotations

import json
from pathlib import Path

from scripts.build_scoring_parity_snapshot import build_snapshot, sync_manifest_scoring_parity_snapshot


def test_build_scoring_parity_snapshot_from_sample_package() -> None:
    package_dir = Path("testdata/package-sample/audit_package/aud_20260311T120000Z_abc1234")
    payload = build_snapshot(package_dir)

    assert payload["methodology_reference"] == "legacy_scoring_weights_v0_2"
    assert payload["overall_status"] == "partial"
    assert [item["level"] for item in payload["levels"]] == [
        "L1_technical",
        "L2_content",
        "L3_semantic",
        "L4_behavioral",
        "L5_ai_interpretability",
    ]
    l4 = next(item for item in payload["levels"] if item["level"] == "L4_behavioral")
    assert l4["status"] == "not_measured"


def test_sync_manifest_scoring_parity_snapshot_upserts_manifest_entry(tmp_path: Path) -> None:
    package_dir = tmp_path / "audit_package" / "aud_20260311T120000Z_abc1234"
    exports_dir = package_dir / "exports"
    exports_dir.mkdir(parents=True)
    manifest = {
        "schema_version": "1.0.0",
        "audit_id": "aud_20260311T120000Z_abc1234",
        "created_at": "2026-03-11T18:00:00Z",
        "ruleset_versions": {"analysis": "mvp-1"},
        "schema_versions": {"manifest": "1.0.0"},
        "stage_status": {"crawl": "completed", "extract": "completed", "analyze": "completed", "package": "completed", "validate": "completed"},
        "files": [],
    }
    (package_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    (exports_dir / "scoring_parity_snapshot.json").write_text('{"schema_version":"1.0.0"}\n', encoding="utf-8")

    sync_manifest_scoring_parity_snapshot(package_dir)

    updated = json.loads((package_dir / "manifest.json").read_text(encoding="utf-8"))
    entry = next(item for item in updated["files"] if item["path"] == "exports/scoring_parity_snapshot.json")
    assert updated["schema_versions"]["scoring_parity_snapshot"] == "1.0.0"
    assert entry["category"] == "export"
    assert entry["schema"] == "scoring_parity_snapshot"
    assert entry["checksum"]
