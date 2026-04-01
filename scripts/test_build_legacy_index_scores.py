from __future__ import annotations

import json
from pathlib import Path

from scripts.build_legacy_index_scores import build_payload


def test_build_legacy_index_scores_from_fixture(tmp_path: Path) -> None:
    package_dir = tmp_path / "audit_package" / "aud_test"
    analysis_dir = package_dir / "analysis"
    analysis_dir.mkdir(parents=True)
    (analysis_dir / "legacy_factor_assessments.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "audit_id": "aud_test",
                "source_method": "fixture",
                "assessments": [
                    {"factor_id": "F-TECH-003", "name": "x", "tier": "core", "level": "L1_technical", "status": "pass", "score": 1.0, "measurement_key": "x", "measurement_value": 1.0, "summary": "x"},
                    {"factor_id": "F-CONT-007", "name": "x", "tier": "core", "level": "L2_content", "status": "partial", "score": 0.5, "measurement_key": "x", "measurement_value": 0.5, "summary": "x"},
                    {"factor_id": "F-SEM-003", "name": "x", "tier": "core", "level": "L3_semantic", "status": "pass", "score": 1.0, "measurement_key": "x", "measurement_value": 1.0, "summary": "x"},
                    {"factor_id": "F-AIO-005", "name": "x", "tier": "core", "level": "L5_ai_interpretability", "status": "partial", "score": 0.5, "measurement_key": "x", "measurement_value": 0.5, "summary": "x"}
                ],
                "summary": {
                    "total_factors": 4,
                    "measured_factors": 4,
                    "unmeasured_factors": 0,
                    "levels_covered": ["L1_technical", "L2_content", "L3_semantic", "L5_ai_interpretability"]
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )

    payload = build_payload(package_dir)

    assert payload["indices"]["ai_readiness"]["score"] > 0
    assert payload["indices"]["generative_visibility"]["score"] > 0
    assert payload["indices"]["answer_fitness"]["score"] > 0
    assert payload["indices"]["ai_readiness"]["coverage"]["measured_factor_count"] == 4
