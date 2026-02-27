from __future__ import annotations

from pathlib import Path


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

