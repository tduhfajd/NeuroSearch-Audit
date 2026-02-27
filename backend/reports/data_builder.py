from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from sqlalchemy.orm import Session

from backend.db.models import Audit, Issue, Page

ISSUE_PRIORITIES = ("P0", "P1", "P2", "P3")


@dataclass(slots=True)
class ReportContext:
    payload: dict[str, object]


def _validate_audit(audit: Audit) -> None:
    if audit.seo_score is None:
        raise ValueError("audit seo_score is required for report generation")
    if audit.avri_score is None:
        raise ValueError("audit avri_score is required for report generation")


def _issue_to_payload(issue: Issue) -> dict[str, object]:
    return {
        "id": issue.id,
        "rule_id": issue.rule_id,
        "priority": issue.priority,
        "title": issue.title,
        "description": issue.description,
        "recommendation": issue.recommendation,
        "affected_url": issue.affected_url,
    }


def _page_to_payload(page: Page) -> dict[str, object]:
    return {
        "id": page.id,
        "url": page.url,
        "status_code": page.status_code,
        "title": page.title,
        "h1": page.h1,
        "meta_description": page.meta_description,
        "inlinks_count": page.inlinks_count,
        "word_count": page.word_count,
        "pagespeed_score": page.pagespeed_score,
    }


def build_report_context(db: Session, audit_id: int) -> ReportContext:
    audit = db.get(Audit, audit_id)
    if audit is None:
        raise LookupError(f"audit {audit_id} not found")
    _validate_audit(audit)

    issues = (
        db.query(Issue)
        .filter(Issue.audit_id == audit_id)
        .order_by(Issue.priority.asc(), Issue.id.asc())
        .all()
    )
    top_pages = (
        db.query(Page)
        .filter(Page.audit_id == audit_id)
        .order_by(Page.inlinks_count.desc(), Page.url.asc())
        .limit(10)
        .all()
    )

    by_priority: dict[str, list[dict[str, object]]] = {priority: [] for priority in ISSUE_PRIORITIES}
    priority_counts: Counter[str] = Counter()
    for issue in issues:
        if issue.priority not in by_priority:
            continue
        by_priority[issue.priority].append(_issue_to_payload(issue))
        priority_counts[issue.priority] += 1

    payload = {
        "audit": {
            "id": audit.id,
            "url": audit.url,
            "client_name": audit.client_name,
            "niche": audit.niche,
            "region": audit.region,
            "goal": audit.goal,
            "status": audit.status,
            "seo_score": float(audit.seo_score),
            "avri_score": float(audit.avri_score),
            "pages_crawled": audit.pages_crawled,
            "created_at": audit.created_at,
            "completed_at": audit.completed_at,
        },
        "facts": {
            "issues_total": len(issues),
            "by_priority_count": {priority: priority_counts.get(priority, 0) for priority in ISSUE_PRIORITIES},
            "top_pages_total": len(top_pages),
        },
        "issue_map": by_priority,
        "top_pages": [_page_to_payload(page) for page in top_pages],
    }
    return ReportContext(payload=payload)

