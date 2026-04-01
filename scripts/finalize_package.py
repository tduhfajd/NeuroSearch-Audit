#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from python.common.validators import validate_contracts, validate_evidence, validate_prompts


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 scripts/finalize_package.py <audit_package_dir>", file=sys.stderr)
        return 1

    package_dir = Path(argv[1])
    issues = validate_contracts(package_dir) + validate_evidence(package_dir) + validate_prompts(package_dir)
    if issues:
        print("package rejected")
        for issue in issues:
            print(f"- {issue.path}: {issue.message}")
        return 1

    print("package approved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
