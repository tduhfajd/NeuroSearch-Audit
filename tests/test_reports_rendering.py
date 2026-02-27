from __future__ import annotations

from pathlib import Path

from backend.reports.generator import deterministic_filename, html_to_pdf_bytes, render_html


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_template_sections_full_report() -> None:
    html = _read("backend/reports/templates/report_full.html")

    assert "Executive Summary" in html
    assert "Tech Health" not in html  # moved to partial include
    assert '{% include "partials/_metrics_cards.html" %}' in html
    assert '{% include "partials/_issue_map.html" %}' in html
    assert "Recommendations" in html


def test_kp_template_sections_and_fields() -> None:
    html = _read("backend/reports/templates/report_kp.html")

    assert "Коммерческое предложение" in html
    assert "Выбранный пакет" in html
    assert "Объем работ" in html
    assert "Ожидаемый эффект" in html
    assert "{{ package.package_name }}" in html


def test_pdf_generation_returns_pdf_bytes_with_fallback() -> None:
    html = "<html><body><h1>Report</h1></body></html>"

    payload = html_to_pdf_bytes(html)

    assert isinstance(payload, bytes)
    assert payload.startswith(b"%PDF")
    assert len(payload) > 100


def test_cyrillic_rendering_is_present_in_html_output() -> None:
    context = {
        "audit": {"url": "https://example.com", "seo_score": 78.0, "avri_score": 63.0},
        "facts": {"by_priority_count": {"P0": 1, "P1": 2, "P2": 0, "P3": 0}},
        "executive_summary": "Краткий итог аудита.",
        "recommendations": ["Добавить schema.org", "Усилить E-E-A-T сигналы"],
    }

    html = render_html("report_full.html", context)

    assert "Executive Summary" in html
    assert "Tech Health" in html
    assert "AI Readiness" in html
    assert "Recommendations" in html
    assert "Краткий итог аудита." in html


def test_deterministic_filename_format() -> None:
    filename = deterministic_filename(42, "full_report")

    assert filename.startswith("audit_42_full_report_")
    assert filename.endswith(".pdf")


def test_template_sections_and_valid_pdf_smoke() -> None:
    context = {
        "audit": {
            "url": "https://example.com",
            "client_name": "ООО Тест",
            "seo_score": 72.0,
            "avri_score": 58.0,
        },
        "facts": {"by_priority_count": {"P0": 0, "P1": 1, "P2": 2, "P3": 3}},
        "package": {"package_name": "Growth", "rationale": "Есть P1 и P2"},
        "executive_summary": "Сайт требует точечной технической доработки.",
        "recommendations": ["Исправить canonical", "Добавить FAQ schema"],
        "work_scope": ["Технические фиксы", "Контентная оптимизация"],
        "expected_impact": "Рост качества индексации и AI-видимости",
    }

    report_html = render_html("report_full.html", context)
    kp_html = render_html("report_kp.html", context)

    assert "Issue Map" in report_html
    assert "Recommendations" in report_html
    assert "Коммерческое предложение" in kp_html
    assert "Выбранный пакет" in kp_html

    report_pdf = html_to_pdf_bytes(report_html)
    kp_pdf = html_to_pdf_bytes(kp_html)
    assert report_pdf.startswith(b"%PDF")
    assert kp_pdf.startswith(b"%PDF")
