from __future__ import annotations

import json
from pathlib import Path

from scripts.export_package import sync_manifest_exports


def test_sync_manifest_exports_upserts_export_entries(tmp_path: Path) -> None:
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
    (exports_dir / "summary.json").write_text('{"audit_id":"aud_20260311T120000Z_abc1234","status":{"crawl":"completed","extract":"completed","analyze":"completed","package":"completed","validate":"completed"},"lead_value_index":0,"top_gaps":[],"high_contradictions":[],"package_status":"approved"}\n', encoding="utf-8")
    (exports_dir / "backlog.json").write_text('{"audit_id":"aud_20260311T120000Z_abc1234","items":[]}\n', encoding="utf-8")

    sync_manifest_exports(package_dir)

    updated = json.loads((package_dir / "manifest.json").read_text(encoding="utf-8"))
    summary_entry = next(item for item in updated["files"] if item["path"] == "exports/summary.json")
    backlog_entry = next(item for item in updated["files"] if item["path"] == "exports/backlog.json")
    assert updated["schema_versions"]["export_summary"] == "1.0.0"
    assert updated["schema_versions"]["export_backlog"] == "1.0.0"
    assert summary_entry["category"] == "export"
    assert backlog_entry["category"] == "export"
    assert summary_entry["required"] is False
    assert backlog_entry["required"] is False
    assert summary_entry["schema"] == "export_summary"
    assert backlog_entry["schema"] == "export_backlog"
