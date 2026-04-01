from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_commercial_documents import (
    build_commercial_offer,
    build_technical_action_plan,
    render_commercial_offer_md,
    render_technical_action_plan_md,
)


def test_generate_commercial_documents_from_fixture(tmp_path: Path) -> None:
    package_dir = tmp_path / "audit_package" / "aud_test"
    exports_dir = package_dir / "exports"
    analysis_dir = package_dir / "analysis"
    exports_dir.mkdir(parents=True)
    analysis_dir.mkdir()
    (exports_dir / "review_brief.json").write_text(
        json.dumps(
            {
                "audit_id": "aud_test",
                "package_status": "approved",
                "top_gaps": ["secure_protocol", "proof", "messengers"],
                "priority_pages": [{"url": "https://example.com/"}],
                "crawl_quality": {"warnings": ["http and https variants found"]},
            },
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (exports_dir / "client_report_input.json").write_text(
        json.dumps(
            {
                "site": {"primary_domain": "example.com", "primary_url": "https://example.com", "site_profile": "service"}
            },
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (analysis_dir / "recommendations.json").write_text(
        json.dumps(
            {
                "recommendations": [
                    {
                        "title": "Redirect all http URLs to https",
                        "priority": "P0",
                        "acceptance_criteria": ["Настроить 301/308 редирект", "Обновить canonical на https"],
                        "expected_impact": "Снижение протокольных рисков и рост доверия.",
                    }
                ]
            },
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )

    offer = build_commercial_offer(package_dir)
    plan = build_technical_action_plan(package_dir)
    offer_md = render_commercial_offer_md(offer)
    plan_md = render_technical_action_plan_md(plan)

    assert offer["recommended_package"]
    assert "## 3. Рекомендуемый стартовый пакет" in offer_md
    assert plan["tasks"][0]["priority"] == "P0"
    assert plan["tasks"][0]["problem_statement"]
    assert plan["tasks"][0]["where_to_change"]
    assert "### TASK-01" in plan_md
    assert "Что видим сейчас" in plan_md
    assert "Где менять" in plan_md
    assert "AI-ready" not in offer_md
    assert "entity/trust/answer-ready" not in offer_md
