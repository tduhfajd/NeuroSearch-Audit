from __future__ import annotations

from pathlib import Path
import json
import sys

from python.analysis.findings import build_contradictions, build_coverage
from python.common.contracts import load_json


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: python -m python.analysis.findings_cli <entities.json> <facts.json>", file=sys.stderr)
        return 1

    entities = load_json(Path(argv[1]))
    facts = load_json(Path(argv[2]))
    audit_id = entities["audit_id"]

    coverage = build_coverage(audit_id, entities, facts)
    contradictions = build_contradictions(audit_id, entities, facts)
    print(
        json.dumps(
            {
                "coverage_report": coverage.to_json(),
                "contradictions": contradictions.to_json(),
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
