from __future__ import annotations

from backend.analyzer.rules import IssueCandidate

AVRI_METRIC_KEYS = (
    "answer_format",
    "structure_density",
    "definition_coverage",
    "authority_signals",
    "schema_need",
)

AVRI_WEIGHTS: dict[str, float] = {
    "answer_format": 0.25,
    "structure_density": 0.20,
    "definition_coverage": 0.20,
    "authority_signals": 0.20,
    "schema_need": 0.15,
}

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


def calculate_avri_score(metric_rows: list[dict[str, float]]) -> float | None:
    if not metric_rows:
        return None

    averages = {
        metric_key: sum(row[metric_key] for row in metric_rows) / len(metric_rows)
        for metric_key in AVRI_METRIC_KEYS
    }
    avri_10 = sum(averages[key] * AVRI_WEIGHTS[key] for key in AVRI_METRIC_KEYS)
    return round(max(0.0, min(100.0, avri_10 * 10)), 2)
