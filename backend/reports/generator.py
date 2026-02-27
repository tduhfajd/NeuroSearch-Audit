from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def _render_via_jinja(template_name: str, context: dict[str, Any]) -> str:
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("jinja2 is not available") from exc

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template(template_name)
    return template.render(**context)


def _render_fallback(template_name: str, context: dict[str, Any]) -> str:
    audit = context.get("audit", {})
    facts = context.get("facts", {})
    package = context.get("package", {})
    executive_summary = context.get("executive_summary", "")
    recommendations = context.get("recommendations", [])
    work_scope = context.get("work_scope", [])
    expected_impact = context.get("expected_impact", "")
    counts = facts.get("by_priority_count", {"P0": 0, "P1": 0, "P2": 0, "P3": 0})

    if template_name == "report_full.html":
        return f"""<!doctype html>
<html lang="ru">
  <head><meta charset="utf-8" /><title>Отчет аудита</title></head>
  <body>
    <h1>Executive Summary</h1>
    <p>{executive_summary}</p>
    <h2>Tech Health</h2><p>SEO Score: {audit.get("seo_score")}</p>
    <h2>AI Readiness</h2><p>AVRI: {audit.get("avri_score")}</p>
    <h2>Issue Map</h2>
    <p>
      P0: {counts.get("P0", 0)} | P1: {counts.get("P1", 0)} | P2: {counts.get("P2", 0)}
      | P3: {counts.get("P3", 0)}
    </p>
    <h2>Recommendations</h2>
    <ul>{"".join(f"<li>{item}</li>" for item in recommendations)}</ul>
  </body>
</html>"""

    return f"""<!doctype html>
<html lang="ru">
  <head><meta charset="utf-8" /><title>Коммерческое предложение</title></head>
  <body>
    <h1>Коммерческое предложение</h1>
    <p>Клиент: {audit.get("client_name") or audit.get("url")}</p>
    <h2>Выбранный пакет</h2><p>{package.get("package_name")}</p><p>{package.get("rationale")}</p>
    <h2>Объем работ</h2><ul>{"".join(f"<li>{item}</li>" for item in work_scope)}</ul>
    <h2>Ожидаемый эффект</h2><p>{expected_impact}</p>
  </body>
</html>"""


def render_html(template_name: str, context: dict[str, Any]) -> str:
    try:
        return _render_via_jinja(template_name, context)
    except RuntimeError:
        return _render_fallback(template_name, context)


def _minimal_pdf_bytes(text: str) -> bytes:
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 40 750 Td ({escaped[:1000]}) Tj ET"
    pdf = (
        "%PDF-1.4\n"
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        "/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
        "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        f"5 0 obj << /Length {len(stream)} >> stream\n{stream}\nendstream endobj\n"
        "xref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000062 00000 n \n"
        "0000000119 00000 n \n0000000248 00000 n \n0000000318 00000 n \n"
        "trailer << /Size 6 /Root 1 0 R >>\nstartxref\n420\n%%EOF\n"
    )
    return pdf.encode("latin-1", errors="ignore")


def html_to_pdf_bytes(html: str) -> bytes:
    try:
        from weasyprint import HTML
    except Exception:  # noqa: BLE001
        return _minimal_pdf_bytes("NeuroSearch report")

    return HTML(string=html).write_pdf()


def deterministic_filename(audit_id: int, report_type: str, now: datetime | None = None) -> str:
    ts = (now or datetime.now(UTC)).strftime("%Y%m%d_%H%M%S")
    return f"audit_{audit_id}_{report_type}_{ts}.pdf"
