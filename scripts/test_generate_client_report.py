from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_client_report import build_client_report, render_markdown, sync_manifest_client_report


def test_build_client_report_from_sample_input() -> None:
    report_input = json.loads(
        Path("testdata/package-sample/audit_package/aud_20260311T120000Z_abc1234/exports/client_report_input.json").read_text(
            encoding="utf-8"
        )
    )
    report = build_client_report(report_input)

    assert report["package_status"] == "approved"
    assert report["methodology"]["score_parity"] == "not_aligned"
    assert report["sections"]["index_reading_guide"]
    assert report["sections"]["indices"]
    assert report["sections"]["priority_areas"]
    assert report["sections"]["priority_area_narratives"]
    assert report["sections"]["action_plan"]
    assert report["sections"]["how_to_use"]


def test_render_client_report_markdown_contains_legacy_sections() -> None:
    report_input = json.loads(
        Path("testdata/package-sample/audit_package/aud_20260311T120000Z_abc1234/exports/client_report_input.json").read_text(
            encoding="utf-8"
        )
    )
    report = build_client_report(report_input)
    markdown = render_markdown(report)

    assert "# Краткий вывод" in markdown
    assert "# Что оценивалось" in markdown
    assert "# Как читать индексы" in markdown
    assert "# Сводные индексы состояния" in markdown
    assert "# Ключевые зоны улучшений" in markdown
    assert "# План действий" in markdown
    assert "# Как использовать этот отчёт" in markdown
    assert "Методологическая оговорка" in markdown
    assert "legacy-style весовой модели" in markdown
    assert "legacy NeuroSearch" not in markdown
    assert "AI Readiness" in markdown
    assert "Generative Visibility" in markdown
    assert "Answer Fitness" in markdown
    assert "SEO |" not in markdown
    assert "понятные контакты" in markdown
    assert "- contacts" not in markdown
    assert "AI-readiness" not in markdown
    assert "agentic" not in markdown


def test_sync_manifest_client_report_upserts_entries(tmp_path: Path) -> None:
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
    (exports_dir / "client_report_input.json").write_text('{"schema_version":"1.0.0","audit_id":"aud_20260311T120000Z_abc1234","package_status":"approved","methodology":{"score_engine":"current_deterministic_coverage_scoring_v1","legacy_reference":"legacy_scoring_weights_v0_2","report_parity":"partial","score_parity":"not_aligned"},"site":{"primary_domain":"example.com","primary_url":"https://example.com/service","site_profile":"service"},"summary":{"overview":"x","primary_risk":"x","primary_opportunity":"x","next_step":"x","page_count":1,"p0_coverage_targets":1,"high_contradiction_count":0},"indices":{"lead_value_index":0.1,"dimensions":{"SEO":0.1,"GEO":0.1,"AEO":0.1,"AIO":0.1,"LEO":0.1},"legacy_scores":[{"key":"ai_readiness","label":"AI Readiness","score":0.45,"description":"x","measured_factor_count":4,"total_factor_count":10,"levels_covered":["L1_technical"]},{"key":"generative_visibility","label":"Generative Visibility","score":0.38,"description":"x","measured_factor_count":3,"total_factor_count":10,"levels_covered":["L1_technical"]},{"key":"answer_fitness","label":"Answer Fitness","score":0.56,"description":"x","measured_factor_count":5,"total_factor_count":10,"levels_covered":["L2_content"]}]},"strengths":[],"priority_areas":[],"action_plan":[],"constraints":[],"evidence_sources":["https://example.com/service"]}\n', encoding="utf-8")
    (exports_dir / "client_report.json").write_text('{"schema_version":"1.0.0","audit_id":"aud_20260311T120000Z_abc1234","package_status":"approved","methodology":{"score_engine":"current_deterministic_coverage_scoring_v1","legacy_reference":"legacy_scoring_weights_v0_2","report_parity":"partial","score_parity":"not_aligned"},"title":"Аудит сайта example.com","site":{"primary_domain":"example.com","primary_url":"https://example.com/service","site_profile":"service"},"sections":{"executive_summary":["x"],"what_was_evaluated":[{"label":"AI Readiness","description":"x"}],"index_reading_guide":["x"],"indices":[{"label":"AI Readiness","value":45.0,"interpretation":"зона улучшений"}],"strengths":[],"priority_areas":[],"priority_area_narratives":[],"action_plan":[],"constraints":[],"how_to_use":[{"audience":"Руководитель","guidance":"x"}]}}\n', encoding="utf-8")

    sync_manifest_client_report(package_dir)

    updated = json.loads((package_dir / "manifest.json").read_text(encoding="utf-8"))
    assert updated["schema_versions"]["client_report_input"] == "1.0.0"
    assert updated["schema_versions"]["client_report"] == "1.0.0"
    assert any(item["path"] == "exports/client_report_input.json" and item["schema"] == "client_report_input" for item in updated["files"])
    assert any(item["path"] == "exports/client_report.json" and item["schema"] == "client_report" for item in updated["files"])
