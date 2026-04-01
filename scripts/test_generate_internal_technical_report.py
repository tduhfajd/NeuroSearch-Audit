from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_internal_technical_report import build_report, render_markdown


def test_generate_internal_technical_report_from_fixture(tmp_path: Path) -> None:
    package_dir = tmp_path / "audit_package" / "aud_test"
    exports_dir = package_dir / "exports"
    technical_dir = package_dir / "pages" / "technical"
    exports_dir.mkdir(parents=True)
    technical_dir.mkdir(parents=True)

    (exports_dir / "review_brief.json").write_text(
        json.dumps(
            {
                "audit_id": "aud_test",
                "package_status": "approved",
                "crawl_quality": {"warnings": ["crawl included non-html fetches"]},
                "high_contradictions": [
                    {
                        "type": "contact_phone_conflict",
                        "severity": "high",
                        "sources": ["https://example.com/", "https://example.com/contact"],
                        "risk": ["trust", "lead_quality"],
                    }
                ],
                "priority_recommendations": [
                    {
                        "priority": "P0",
                        "expected_impact": "Improve protocol trust",
                        "acceptance_criteria": [
                            "Redirect all http URLs to https with a permanent 301/308 response",
                            "Enable Strict-Transport-Security on HTTPS responses",
                        ],
                    }
                ],
            },
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (exports_dir / "client_report_input.json").write_text(
        json.dumps(
            {
                "site": {"primary_domain": "example.com", "primary_url": "https://example.com", "site_profile": "service"},
                "constraints": ["Отчет зависит от полноты crawl-данных."],
            },
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (technical_dir / "example.com_.json").write_text(
        json.dumps(
            {
                "url": "https://example.com/",
                "title": "",
                "meta": {"description": ""},
                "headings": {"h1": []},
                "canonical_url": "http://example.com/",
                "transport_signals": {"strict_transport_security": "", "mixed_content_urls": ["http://example.com/app.js"]},
            },
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_report(package_dir)
    markdown = render_markdown(report)

    assert report["technical_summary"]
    assert report["contradictions"][0]["title"] == "Конфликт контактных телефонов"
    assert "## 2. Сводка технических проблем" in markdown
    assert "## 3. Противоречия в данных сайта" in markdown
    assert "Strict-Transport-Security" in markdown
