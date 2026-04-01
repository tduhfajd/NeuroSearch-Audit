#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean generated audit artifacts without touching source files."
    )
    parser.add_argument(
        "--include-caches",
        action="store_true",
        help="Also remove Python caches such as __pycache__ and .pytest_cache",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Apply cleanup immediately without extra confirmation",
    )
    return parser.parse_args()


def collect_targets(include_caches: bool) -> list[Path]:
    targets = [
        ROOT / "audit_package",
        ROOT / "runtime",
        ROOT / "out",
        ROOT / "latest_reports",
    ]
    if include_caches:
        targets.extend(
            [
                ROOT / ".pytest_cache",
                ROOT / "__pycache__",
                ROOT / "scripts" / "__pycache__",
                ROOT / "reportgen" / "__pycache__",
                ROOT / "python" / "analysis" / "__pycache__",
                ROOT / "python" / "common" / "__pycache__",
                ROOT / "python" / "semantic" / "__pycache__",
            ]
        )
    return [path for path in targets if path.exists()]


def main() -> int:
    args = parse_args()
    targets = collect_targets(args.include_caches)

    if not targets:
        print("Nothing to clean.")
        return 0

    print("The following generated paths will be removed:")
    for path in targets:
        print(f"- {path}")

    if not args.yes:
        print("\nRe-run with --yes to apply cleanup.")
        return 0

    for path in targets:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink(missing_ok=True)

    print("Cleanup completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
