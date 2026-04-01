#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys


IGNORED_FIELDS = {"updated_at", "created_at", "rendered_at", "extracted_at", "fetched_at"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(value):
    if isinstance(value, dict):
        return {
            key: normalize(item)
            for key, item in sorted(value.items())
            if key not in IGNORED_FIELDS
        }
    if isinstance(value, list):
        return [normalize(item) for item in value]
    return value


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: python3 scripts/validate_reproducibility.py <baseline.json> <candidate.json>", file=sys.stderr)
        return 1

    left = normalize(load(Path(argv[1])))
    right = normalize(load(Path(argv[2])))

    if left != right:
        print("reproducibility validation failed")
        print(json.dumps({"baseline": left, "candidate": right}, ensure_ascii=True, indent=2))
        return 1

    print("reproducibility validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
