from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_review_artifacts import build_review_brief, render_markdown, sync_manifest_review_brief


def test_review_brief_includes_executive_summary_and_action_plan() -> None:
    package_dir = Path("testdata/package-sample/audit_package/aud_20260311T120000Z_abc1234")
    brief = build_review_brief(package_dir)

    assert brief["executive_summary"]["site_profile"] in {"service", "ecommerce", "mixed"}
    assert brief["executive_summary"]["overview"]
    assert brief["executive_summary"]["next_step"]
    assert brief["action_plan"]
    assert len(brief["action_plan"]) <= 6
    assert "current_strengths" in brief
    assert "focus_areas" in brief

    markdown = render_markdown(brief)
    assert "## Краткий вывод" in markdown
    assert "## План действий" in markdown
    assert "## Что уже работает" in markdown or brief["current_strengths"] == []
    assert "## Ключевые зоны внимания" in markdown or brief["focus_areas"] == []
    assert "Связанные проблемы" in markdown
    assert "в зоне внимания" in markdown or brief["focus_areas"] == []


def test_review_brief_excludes_fully_covered_generic_pages_from_priority_pages() -> None:
    package_dir = Path("testdata/package-sample/audit_package/aud_20260311T120000Z_abc1234")
    brief = build_review_brief(package_dir)

    assert all(
        not (page["page_type"] == "generic" and page["missing"] == [])
        for page in brief["priority_pages"]
    )


def test_review_brief_reports_protocol_duplication_warning() -> None:
    package_dir = Path("testdata/package-sample/audit_package/aud_20260311T120000Z_abc1234")
    brief = build_review_brief(package_dir)

    assert "protocol_duplication" in brief["crawl_quality"]
    assert brief["crawl_quality"]["protocol_duplication"] is False


def test_sync_manifest_review_brief_upserts_manifest_entry(tmp_path: Path) -> None:
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
    (exports_dir / "review_brief.json").write_text('{"schema_version":"1.0.0"}\n', encoding="utf-8")

    sync_manifest_review_brief(package_dir)

    updated = json.loads((package_dir / "manifest.json").read_text(encoding="utf-8"))
    review_entry = next(item for item in updated["files"] if item["path"] == "exports/review_brief.json")
    assert updated["schema_versions"]["review_brief"] == "1.0.0"
    assert review_entry["category"] == "export"
    assert review_entry["required"] is False
    assert review_entry["schema"] == "review_brief"
    assert review_entry["checksum"]
