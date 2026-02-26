from __future__ import annotations

from backend.analyzer.rules import IssueCandidate

RULE_PENALTY_WEIGHTS: dict[str, float] = {
    "ANA-01": 10.0,
    "ANA-02": 6.0,
    "ANA-03": 4.0,
    "ANA-04": 8.0,
    "ANA-05": 10.0,
    "ANA-06": 5.0,
    "ANA-07": 5.0,
    "ANA-08": 4.0,
}


def calculate_seo_score(issue_candidates: list[IssueCandidate]) -> float:
    score = 100.0
    for issue in issue_candidates:
        score -= RULE_PENALTY_WEIGHTS.get(issue.rule_id, 2.0)
    if score < 0:
        return 0.0
    if score > 100:
        return 100.0
    return round(score, 2)
