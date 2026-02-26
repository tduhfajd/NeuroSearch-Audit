from __future__ import annotations

from dataclasses import dataclass

from backend.analyzer.rules import IssueCandidate, Rule, RuleContext, get_rule_registry
from backend.db.models import Audit, Page


@dataclass(slots=True)
class AnalysisResult:
    issue_candidates: list[IssueCandidate]


def build_context(audit: Audit, pages: list[Page]) -> RuleContext:
    return RuleContext(audit=audit, pages=pages)


def run_rules(context: RuleContext, rules: list[Rule] | None = None) -> list[IssueCandidate]:
    active_rules = rules or get_rule_registry()
    issues: list[IssueCandidate] = []
    for rule in active_rules:
        issues.extend(rule.evaluate(context))
    return issues


def execute_analysis(audit: Audit, pages: list[Page], rules: list[Rule] | None = None) -> AnalysisResult:
    context = build_context(audit=audit, pages=pages)
    issue_candidates = run_rules(context=context, rules=rules)
    return AnalysisResult(issue_candidates=issue_candidates)
