from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_expert_report import build_expert_report, render_markdown


def test_build_expert_report_from_package_fixture(tmp_path: Path) -> None:
    package_dir = tmp_path / "audit_package" / "aud_test"
    exports_dir = package_dir / "exports"
    exports_dir.mkdir(parents=True)
    (exports_dir / "review_brief.json").write_text(
        json.dumps(
            {
                "audit_id": "aud_test",
                "package_status": "approved",
                "top_gaps": ["proof", "secure_protocol", "messengers"],
                "focus_areas": [
                    {
                        "label": "Главная страница и первое доверие",
                        "page_type": "homepage",
                        "top_missing": ["proof", "messengers", "secure_protocol"],
                    }
                ],
                "summary": {"p0_coverage_targets": 1},
                "priority_pages": [{"page_type": "homepage", "url": "https://example.com/"}],
                "constraints": [],
                "crawl_quality": {"protocol_duplication": True},
            },
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (exports_dir / "client_report_input.json").write_text(
        json.dumps(
            {
                "site": {
                    "primary_domain": "example.com",
                    "primary_url": "https://example.com",
                    "site_profile": "service",
                },
                "summary": {"overview": "Аудит показал, что сервисный сайт находится в зоне улучшений."},
                "indices": {
                    "legacy_scores": [
                        {
                            "key": "ai_readiness",
                            "label": "AI Readiness",
                            "score": 0.55,
                            "description": "x",
                            "measured_factor_count": 5,
                            "total_factor_count": 10,
                            "levels_covered": ["L1_technical", "L2_content"],
                        },
                        {
                            "key": "generative_visibility",
                            "label": "Generative Visibility",
                            "score": 0.51,
                            "description": "x",
                            "measured_factor_count": 4,
                            "total_factor_count": 10,
                            "levels_covered": ["L1_technical"],
                        },
                        {
                            "key": "answer_fitness",
                            "label": "Answer Fitness",
                            "score": 0.48,
                            "description": "x",
                            "measured_factor_count": 6,
                            "total_factor_count": 10,
                            "levels_covered": ["L2_content", "L3_semantic"],
                        },
                    ]
                },
                "strengths": ["Есть базовая сервисная структура."],
                "constraints": ["Часть выводов зависит от полноты crawl-данных."],
            },
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_expert_report(package_dir)
    markdown = render_markdown(report)

    assert report["sections"]["limitations"][0]["area"] == "Главная страница и первое доверие"
    assert report["sections"]["priority_workstreams"]
    assert "## Сводные индексы состояния" in markdown
    assert "AI Readiness" in markdown
    assert "Generative Visibility" in markdown
    assert "Answer Fitness" in markdown
    assert "SEO" not in markdown
    assert "## Ключевые ограничения, которые сейчас мешают росту" in markdown
    assert "## Приоритеты работ" in markdown
    assert "coverage-gap" not in markdown
    assert "AI-ready" not in markdown
