from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_technical_client_report import build_report, render_markdown


def test_generate_technical_client_report_from_fixture(tmp_path: Path) -> None:
    package_dir = tmp_path / "audit_package" / "aud_test"
    exports_dir = package_dir / "exports"
    exports_dir.mkdir(parents=True)
    (exports_dir / "review_brief.json").write_text(
        json.dumps(
            {
                "audit_id": "aud_test",
                "package_status": "approved",
                "summary": {"page_count": 5},
                "top_gaps": ["secure_protocol", "proof", "messengers"],
                "priority_pages": [{"url": "https://example.com/"}],
                "priority_recommendations": [
                    {
                        "acceptance_criteria": [
                            "Redirect all http URLs to https with a permanent 301/308 response",
                            "Set canonical URLs to the https version only",
                        ]
                    }
                ],
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
                "site": {"primary_domain": "example.com", "primary_url": "https://example.com", "site_profile": "service"},
                "constraints": ["Текущий отчет зависит от полноты crawl-данных."],
            },
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_report(package_dir)
    markdown = render_markdown(report)

    assert report["issues"][0]["priority"] == "P0"
    assert report["issues"][0]["title"]
    assert report["issues"][0]["what_to_change"]
    assert "## 3. Выявленные недостатки и что с ними делать" in markdown
    assert "## 4. Следующие шаги" in markdown
