#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from python.common.validators import validate_evidence


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 scripts/validate_evidence.py <audit_package_dir>", file=sys.stderr)
        return 1

    package_dir = Path(argv[1])
    issues = validate_evidence(package_dir)
    if issues:
        print("evidence validation failed")
        for issue in issues:
            print(f"- {issue.path}: {issue.message}")
        return 1

    print("evidence validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
