from __future__ import annotations

import json
from pathlib import Path

from scripts.build_client_report_input import build_report_input


def test_build_client_report_input_from_sample_package() -> None:
    package_dir = Path("testdata/package-sample/audit_package/aud_20260311T120000Z_abc1234")
    payload = build_report_input(package_dir)

    assert payload["package_status"] == "approved"
    assert payload["methodology"]["score_engine"] == "current_deterministic_coverage_scoring_v1"
    assert payload["methodology"]["legacy_reference"] == "legacy_scoring_weights_v0_2"
    assert payload["methodology"]["score_parity"] == "not_aligned"
    assert payload["site"]["primary_domain"] == "example.com"
    assert payload["site"]["site_profile"] == "service"
    assert payload["summary"]["p0_coverage_targets"] == 1
    assert payload["indices"]["dimensions"]["SEO"] == 0.29
    assert [item["label"] for item in payload["indices"]["legacy_scores"]] == [
        "AI Readiness",
        "Generative Visibility",
        "Answer Fitness",
    ]
    assert payload["summary"]["overview"].startswith("Аудит показал")
    assert payload["priority_areas"]
    assert payload["action_plan"]
    assert payload["action_plan"][0]["summary"].startswith("Добавить") or payload["action_plan"][0]["summary"].startswith("Настроить")
    assert payload["constraints"]
    assert payload["evidence_sources"] == [
        "https://example.com/service",
        "https://example.com/service/pricing",
    ]


def test_client_report_input_payload_is_json_serializable() -> None:
    package_dir = Path("testdata/package-sample/audit_package/aud_20260311T120000Z_abc1234")
    payload = build_report_input(package_dir)
    serialized = json.dumps(payload, ensure_ascii=True, indent=2)

    assert '"schema_version": "1.0.0"' in serialized
