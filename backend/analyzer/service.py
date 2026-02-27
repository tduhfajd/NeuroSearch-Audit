from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import delete
from sqlalchemy.orm import Session

from backend.analyzer.rules import IssueCandidate, Rule, RuleContext, get_rule_registry
from backend.analyzer.scoring import calculate_seo_score
from backend.db.models import Audit, Issue, Page


@dataclass(slots=True)
class AnalysisResult:
    issue_candidates: list[IssueCandidate]


@dataclass(slots=True)
class AnalyzeSummary:
    audit_id: int
    issues_created: int
    by_priority: dict[str, int]
    seo_score: float


def build_context(audit: Audit, pages: list[Page]) -> RuleContext:
    return RuleContext(audit=audit, pages=pages)


def run_rules(context: RuleContext, rules: list[Rule] | None = None) -> list[IssueCandidate]:
    active_rules = rules or get_rule_registry()
    issues: list[IssueCandidate] = []
    for rule in active_rules:
        issues.extend(rule.evaluate(context))
    return issues


def execute_analysis(
    audit: Audit,
    pages: list[Page],
    rules: list[Rule] | None = None,
) -> AnalysisResult:
    context = build_context(audit=audit, pages=pages)
    issue_candidates = run_rules(context=context, rules=rules)
    return AnalysisResult(issue_candidates=issue_candidates)


def analyze_audit(db: Session, audit_id: int, rules: list[Rule] | None = None) -> AnalyzeSummary:
    audit = db.get(Audit, audit_id)
    if audit is None:
        raise LookupError(f"audit {audit_id} not found")

    pages = db.query(Page).filter(Page.audit_id == audit_id).all()
    result = execute_analysis(audit=audit, pages=pages, rules=rules)
    seo_score = calculate_seo_score(result.issue_candidates)

    db.execute(delete(Issue).where(Issue.audit_id == audit_id))

    issues_created = 0
    by_priority = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    seen_issue_keys: set[tuple[str, int | None, str | None, str]] = set()
    for candidate in result.issue_candidates:
        priority = candidate.resolve_priority()
        dedupe_key = (candidate.rule_id, candidate.page_id, candidate.affected_url, candidate.title)
        if dedupe_key in seen_issue_keys:
            continue
        seen_issue_keys.add(dedupe_key)
        issue = Issue(
            audit_id=audit_id,
            page_id=candidate.page_id,
            rule_id=candidate.rule_id,
            priority=priority,
            title=candidate.title,
            description=candidate.description,
            recommendation=candidate.recommendation,
            affected_url=candidate.affected_url,
        )
        db.add(issue)
        by_priority[priority] = by_priority.get(priority, 0) + 1
        issues_created += 1

    audit.seo_score = seo_score
    db.flush()
    db.commit()
    return AnalyzeSummary(
        audit_id=audit_id,
        issues_created=issues_created,
        by_priority=by_priority,
        seo_score=seo_score,
    )
