#!/usr/bin/env python3
"""Project validation entrypoint."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from python.common.validators import validate_contracts, validate_evidence, validate_prompts
from scripts.validate_reproducibility import normalize, load as load_reproducibility_json


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    note: str


PACKAGE_FIXTURE = Path("testdata/package-sample/audit_package/aud_20260311T120000Z_abc1234")
REPRO_BASELINE = Path("testdata/fixtures/reproducibility/run_a.json")
REPRO_CANDIDATE = Path("testdata/fixtures/reproducibility/run_b.json")


def main() -> int:
    print("NeuroSearch validation baseline")

    checks: list[Check] = []

    contract_issues = validate_contracts(PACKAGE_FIXTURE)
    checks.append(
        Check(
            name="contracts",
            status="pass" if not contract_issues else "fail",
            note="Validates required files, schema-backed JSON contracts, and manifest inventory against the package fixture.",
        )
    )

    evidence_issues = validate_evidence(PACKAGE_FIXTURE)
    checks.append(
        Check(
            name="evidence",
            status="pass" if not evidence_issues else "fail",
            note="Validates evidence presence for high-priority findings on the package fixture.",
        )
    )

    checks.append(
        Check(
            name="prompts",
            status="pass" if not validate_prompts(PACKAGE_FIXTURE) else "fail",
            note="Validates prompt structure and no-fabrication sections on the package fixture.",
        )
    )
    reproducible = normalize(load_reproducibility_json(REPRO_BASELINE)) == normalize(load_reproducibility_json(REPRO_CANDIDATE))
    checks.append(
        Check(
            name="reproducibility",
            status="pass" if reproducible else "fail",
            note="Validates deterministic output equivalence while ignoring approved timestamp fields.",
        )
    )

    failed = False
    for check in checks:
        print(f"- {check.name}: {check.status} - {check.note}")
        if check.status == "fail":
            failed = True

    prompt_issues = validate_prompts(PACKAGE_FIXTURE)

    for issue in contract_issues + evidence_issues + prompt_issues:
        print(f"  issue: {issue.path} - {issue.message}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
