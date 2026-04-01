#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


RUNTIME_DIRS = ("runtime", "runtime_batches")


@dataclass(slots=True)
class CleanupCandidate:
    kind: str
    path: Path
    age_days: int

    def to_json(self, root: Path) -> dict:
        return {
            "kind": self.kind,
            "path": self.path.relative_to(root).as_posix(),
            "age_days": self.age_days,
        }


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def directory_age_days(path: Path, now: datetime) -> int:
    modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return max(0, int((now - modified_at).total_seconds() // 86400))


def iter_cleanup_candidates(root: Path, retention_days: int, now: datetime) -> list[CleanupCandidate]:
    candidates: list[CleanupCandidate] = []

    runtime_root = root / "runtime"
    if runtime_root.exists():
        for attempt_dir in sorted(runtime_root.glob("*/attempts/*")):
            if not attempt_dir.is_dir():
                continue
            age_days = directory_age_days(attempt_dir, now)
            if age_days < retention_days:
                continue
            candidates.append(CleanupCandidate(kind="runtime_attempt", path=attempt_dir, age_days=age_days))

    batch_root = root / "runtime_batches"
    if batch_root.exists():
        for batch_dir in sorted(batch_root.glob("*")):
            if not batch_dir.is_dir():
                continue
            age_days = directory_age_days(batch_dir, now)
            if age_days < retention_days:
                continue
            candidates.append(CleanupCandidate(kind="runtime_batch", path=batch_dir, age_days=age_days))

    return candidates


def prune_empty_runtime_dirs(root: Path) -> None:
    runtime_root = root / "runtime"
    if runtime_root.exists():
        for parent in sorted(runtime_root.glob("*/attempts")):
            if parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
                audit_dir = parent.parent
                if audit_dir.is_dir() and not any(audit_dir.iterdir()):
                    audit_dir.rmdir()
        if runtime_root.is_dir() and not any(runtime_root.iterdir()):
            runtime_root.rmdir()

    batch_root = root / "runtime_batches"
    if batch_root.is_dir() and not any(batch_root.iterdir()):
        batch_root.rmdir()


def cleanup_runtime(root: Path, retention_days: int, apply: bool, now: datetime) -> dict:
    candidates = iter_cleanup_candidates(root, retention_days, now)
    deleted: list[CleanupCandidate] = []

    if apply:
        for candidate in candidates:
            shutil.rmtree(candidate.path, ignore_errors=False)
            deleted.append(candidate)
        prune_empty_runtime_dirs(root)

    return {
        "root": str(root),
        "retention_days": retention_days,
        "apply": apply,
        "candidates": [item.to_json(root) for item in candidates],
        "deleted": [item.to_json(root) for item in deleted],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean up stale runtime and runtime batch leftovers without touching audit_package.")
    parser.add_argument("root", help="output root containing runtime/ and runtime_batches/")
    parser.add_argument("--retention-days", type=int, default=7, help="minimum age in days before deletion candidates are eligible")
    parser.add_argument("--apply", action="store_true", help="actually delete eligible directories; default is dry-run")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.retention_days < 0:
        raise SystemExit("retention-days must be >= 0")

    root = Path(args.root).resolve()
    result = cleanup_runtime(root=root, retention_days=args.retention_days, apply=args.apply, now=utc_now())
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
