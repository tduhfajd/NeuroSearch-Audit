from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from backend.analyzer.ai_bridge import session_health
from backend.db.models import Page, Report
from backend.reports.data_builder import build_report_context
from backend.reports.generator import deterministic_filename, html_to_pdf_bytes, render_html
from backend.reports.package_selector import choose_package

REPORTS_DIR = Path("generated_reports")


class ReportServiceError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(slots=True)
class ReportGenerationResult:
    audit_id: int
    report_type: str
    file_path: Path
    file_name: str
    generated_at: datetime


def _extract_ai_text(db: Session, audit_id: int) -> tuple[str, list[str]]:
    pages = (
        db.query(Page)
        .filter(Page.audit_id == audit_id)
        .order_by(Page.inlinks_count.desc(), Page.url.asc())
        .limit(10)
        .all()
    )
    recommendations: list[str] = []
    for page in pages:
        payload = page.ai_scores or {}
        if not isinstance(payload, dict):
            continue
        value = payload.get("recommendations")
        if isinstance(value, str) and value.strip():
            recommendations.append(value.strip())
    if not recommendations:
        raise ReportServiceError(
            "ai_text_unavailable", "AI recommendations are required for reports"
        )

    executive_summary = (
        "AI-анализ подтверждает потенциал роста видимости "
        "при устранении приоритетных технических проблем."
    )
    return executive_summary, recommendations[:5]


def generate_report_artifact(
    db: Session,
    *,
    audit_id: int,
    report_type: str,
    storage_dir: Path = REPORTS_DIR,
) -> ReportGenerationResult:
    ok, detail = session_health()
    if not ok:
        raise ReportServiceError("reauth_required", detail)

    if report_type not in {"full_report", "kp"}:
        raise ReportServiceError("invalid_report_type", "Unsupported report type")

    context = build_report_context(db, audit_id).payload
    executive_summary, recommendations = _extract_ai_text(db, audit_id)
    counts = context["facts"]["by_priority_count"]
    package = choose_package(
        p0_count=int(counts["P0"]),
        p1_count=int(counts["P1"]),
        p2_count=int(counts["P2"]),
    )

    template_context = {
        **context,
        "executive_summary": executive_summary,
        "recommendations": recommendations,
        "package": {
            "package_name": package.package_name,
            "rationale": package.rationale,
            "trigger_metrics": package.trigger_metrics,
        },
        "work_scope": [
            "Техническая оптимизация критичных страниц",
            "Контентная доработка структуры ответов",
            "Внедрение schema.org и trust-сигналов",
        ],
        "expected_impact": "Повышение качества индексации и вероятности попадания в AI-ответы.",
    }

    template_name = "report_full.html" if report_type == "full_report" else "report_kp.html"
    html = render_html(template_name, template_context)
    pdf_bytes = html_to_pdf_bytes(html)

    storage_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(UTC)
    file_name = deterministic_filename(audit_id, report_type, now=generated_at)
    file_path = storage_dir / file_name
    file_path.write_bytes(pdf_bytes)

    db.add(
        Report(
            audit_id=audit_id,
            type=report_type,
            file_path=str(file_path),
        )
    )
    db.commit()

    return ReportGenerationResult(
        audit_id=audit_id,
        report_type=report_type,
        file_path=file_path,
        file_name=file_name,
        generated_at=generated_at,
    )
