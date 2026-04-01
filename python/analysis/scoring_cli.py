from __future__ import annotations

from pathlib import Path
import json
import sys

from python.analysis.scoring import build_recommendations, build_scores
from python.common.contracts import load_json


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(
            "usage: python -m python.analysis.scoring_cli <entities.json> <coverage_report.json> <contradictions.json>",
            file=sys.stderr,
        )
        return 1

    entities = load_json(Path(argv[1]))
    coverage = load_json(Path(argv[2]))
    contradictions = load_json(Path(argv[3]))
    audit_id = entities["audit_id"]

    scores = build_scores(audit_id, entities, coverage, contradictions)
    recommendations = build_recommendations(audit_id, coverage, contradictions)
    print(
        json.dumps(
            {
                "scores": scores.to_json(),
                "recommendations": recommendations.to_json(),
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
