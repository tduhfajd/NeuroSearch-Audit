from __future__ import annotations

import json
from pathlib import Path

from scripts.build_legacy_factor_assessments import build_payload


def test_build_legacy_factor_assessments_from_fixture(tmp_path: Path) -> None:
    package_dir = tmp_path / "audit_package" / "aud_test"
    exports_dir = package_dir / "exports"
    analysis_dir = package_dir / "analysis"
    pages_dir = package_dir / "pages" / "technical"
    render_dir = package_dir / "render"
    crawl_dir = package_dir / "crawl"
    exports_dir.mkdir(parents=True)
    analysis_dir.mkdir()
    pages_dir.mkdir(parents=True)
    render_dir.mkdir()
    crawl_dir.mkdir()

    (package_dir / "manifest.json").write_text(json.dumps({"audit_id": "aud_test"}) + "\n", encoding="utf-8")
    (exports_dir / "review_brief.json").write_text(
        json.dumps(
            {
                "summary": {"page_count": 2},
                "crawl_quality": {"protocol_duplication": True},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (analysis_dir / "entities.json").write_text(
        json.dumps(
            {
                "entities": [
                    {"type": "page", "attributes": {"page_type": "homepage"}},
                    {"type": "page", "attributes": {"page_type": "generic"}},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (analysis_dir / "page_blocks.json").write_text(
        json.dumps(
            {
                "pages": [
                    {"blocks": [{"type": "definition", "present": True}, {"type": "faq", "present": False}, {"type": "process_steps", "present": True}, {"type": "contacts", "present": True}, {"type": "legal_trust", "present": True}]},
                    {"blocks": [{"type": "definition", "present": False}, {"type": "faq", "present": True}, {"type": "process_steps", "present": False}, {"type": "proof", "present": False}]},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (render_dir / "render_plan.json").write_text(
        json.dumps({"summary": {"total_pages": 2, "render_required_count": 0}}) + "\n",
        encoding="utf-8",
    )
    (crawl_dir / "fetch_log.json").write_text(
        json.dumps(
            {
                "entries": [
                    {"url": "https://example.com/", "normalized_url": "https://example.com/", "depth": 0, "status": "fetched", "status_code": 200, "content_type": "text/html; charset=UTF-8", "fetched_at": "2026-03-13T09:00:00Z"},
                    {"url": "https://example.com/service", "normalized_url": "https://example.com/service", "depth": 1, "status": "fetched", "status_code": 200, "content_type": "text/html; charset=UTF-8", "fetched_at": "2026-03-13T09:00:01Z"},
                    {"url": "https://example.com/missing", "normalized_url": "https://example.com/missing", "depth": 4, "status": "fetched", "status_code": 404, "content_type": "text/html; charset=UTF-8", "fetched_at": "2026-03-13T09:00:02Z"},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (pages_dir / "one.json").write_text(json.dumps({"schema_hints": ["Organization"], "headings": {"h1": ["Главная"], "h2": ["Услуги"]}}) + "\n", encoding="utf-8")
    (pages_dir / "two.json").write_text(json.dumps({"schema_hints": [], "headings": {"h1": [], "h2": []}}) + "\n", encoding="utf-8")

    payload = build_payload(package_dir)
    assessments = {item["factor_id"]: item for item in payload["assessments"]}

    assert payload["summary"]["total_factors"] == 16
    assert assessments["F-TECH-002"]["status"] == "fail"
    assert assessments["F-TECH-003"]["status"] == "pass"
    assert assessments["F-TECH-004"]["status"] == "fail"
    assert assessments["F-TECH-006"]["status"] == "pass"
    assert assessments["F-CONT-004"]["status"] == "partial"
    assert assessments["F-CONT-005"]["status"] == "pass"
    assert assessments["F-SEM-005"]["status"] == "fail"
    assert assessments["F-AIO-004"]["status"] in {"pass", "partial"}
    assert assessments["F-AIO-005"]["status"] in {"pass", "partial"}
    assert assessments["F-CONT-006"]["status"] == "fail"
    assert assessments["F-KG-003"]["status"] == "pass"
    assert assessments["F-AEO-006"]["status"] == "pass"
